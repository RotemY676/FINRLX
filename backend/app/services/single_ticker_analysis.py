"""Single-ticker deep-analysis service.

End-to-end pipeline: yfinance OHLCV + ticker news -> FINRLX features ->
engine ensemble -> 7-strategy walk-forward backtest -> self-contained HTML
report.

Used by both:
- backend/scripts/analyze_ticker.py  (CLI / standalone HTML)
- GET /api/v1/analysis/single-ticker  (FastAPI endpoint)

Importing this module does not touch the DB; the analysis is pure
yfinance + VADER + the existing engine functions in app.services.engines.
"""
from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from html import escape as h
from pathlib import Path

import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.services.engines import ENGINE_FUNCTIONS

_log = logging.getLogger(__name__)

# Chart.js is vendored alongside this module so the generated HTML is
# truly self-contained — opens correctly offline, inside WhatsApp /
# Gmail in-app viewers (which often block third-party scripts), and on
# mobile browsers in file:// origin. If the vendored file is missing
# we fall back to the CDN reference and log a warning, so the report
# still renders when there's an internet connection.
_CHARTJS_PATH = Path(__file__).parent / "_chartjs.min.js"
try:
    _CHARTJS_SCRIPT_TAG = f"<script>{_CHARTJS_PATH.read_text(encoding='utf-8')}</script>"
    _log.info("loaded vendored Chart.js (%d bytes)", _CHARTJS_PATH.stat().st_size)
except (FileNotFoundError, OSError) as e:
    _log.warning(
        "vendored Chart.js missing at %s (%s); falling back to CDN — "
        "reports will require internet to render charts",
        _CHARTJS_PATH, e,
    )
    _CHARTJS_SCRIPT_TAG = (
        '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/'
        'dist/chart.umd.min.js"></script>'
    )


# ── Feature computation (mirrors backend/app/services/features.py) ───────────

def _compute_return(closes: list[float], lookback: int) -> tuple[float | None, str]:
    if len(closes) < lookback + 1:
        return None, "insufficient_data"
    old = closes[-(lookback + 1)]
    new = closes[-1]
    if old == 0:
        return None, "insufficient_data"
    return round((new - old) / old, 6), "ok"


def _compute_volatility(closes: list[float], lookback: int) -> tuple[float | None, str]:
    if len(closes) < lookback + 1:
        return None, "insufficient_data"
    window = closes[-(lookback + 1):]
    returns = [(window[i] - window[i - 1]) / window[i - 1]
               for i in range(1, len(window)) if window[i - 1] != 0]
    if len(returns) < 5:
        return None, "insufficient_data"
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / len(returns)
    return round(math.sqrt(var) * math.sqrt(252), 6), "ok"


def _compute_drawdown(closes: list[float], lookback: int) -> tuple[float | None, str]:
    if len(closes) < lookback:
        return None, "insufficient_data"
    window = closes[-lookback:]
    peak = window[0]
    max_dd = 0.0
    for c in window:
        if c > peak:
            peak = c
        dd = (peak - c) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return round(-max_dd, 6), "ok"


def _compute_relative_volume(volumes: list[int], lookback: int) -> tuple[float | None, str]:
    if len(volumes) < lookback:
        return None, "insufficient_data"
    window = volumes[-lookback:]
    avg = sum(window) / len(window)
    if avg == 0:
        return None, "insufficient_data"
    return round(volumes[-1] / avg, 4), "ok"


def compute_features(
    closes: list[float],
    volumes: list[int],
    news_scores: list[float],
    news_source_exists: bool,
) -> dict[str, tuple[float | None, str]]:
    """Build the feature dict shape that the engine functions expect."""
    feats: dict[str, tuple[float | None, str]] = {}
    feats["return_5d"] = _compute_return(closes, 5)
    feats["return_20d"] = _compute_return(closes, 20)
    feats["return_60d"] = _compute_return(closes, 60)
    feats["volatility_20d"] = _compute_volatility(closes, 20)
    feats["drawdown_20d"] = _compute_drawdown(closes, 20)
    feats["relative_volume_20d"] = _compute_relative_volume(volumes, 20)

    if news_scores:
        avg = sum(news_scores) / len(news_scores)
        feats["news_sentiment_7d"] = (round(avg, 4), "ok")
        feats["news_count_7d"] = (float(len(news_scores)), "ok")
    elif news_source_exists:
        feats["news_sentiment_7d"] = (None, "insufficient_data")
        feats["news_count_7d"] = (0.0, "ok")
    else:
        feats["news_sentiment_7d"] = (None, "insufficient_data")
        feats["news_count_7d"] = (None, "insufficient_data")
    return feats




# ── Data fetch ────────────────────────────────────────────────────────────────

@dataclass
class Bars:
    dates: list[date]
    closes: list[float]
    volumes: list[int]
    highs: list[float]
    lows: list[float]

    @property
    def latest_close(self) -> float | None:
        return self.closes[-1] if self.closes else None

    @property
    def latest_date(self) -> date | None:
        return self.dates[-1] if self.dates else None

    def window_ending(self, end_date: date) -> Bars:
        """Return a view of this series up to and including `end_date`."""
        idx = [i for i, d in enumerate(self.dates) if d <= end_date]
        if not idx:
            return Bars([], [], [], [], [])
        last = idx[-1] + 1
        return Bars(
            self.dates[:last],
            self.closes[:last],
            self.volumes[:last],
            self.highs[:last],
            self.lows[:last],
        )


MIN_COVERAGE = 0.5  # a source must cover >=50% of expected sessions to stand alone


def _expected_sessions(days: int) -> int:
    return max(int(days * 5 / 7 * 0.9), 1)


def _bars_from_stooq(ticker: str, start: date, end: date) -> Bars:
    """Keyless fallback via the F1 stooq provider (Operation Credibility K1).

    The dossier path previously used raw yfinance ONLY; from cloud hosts
    yfinance frequently returns a thin recent window instead of failing,
    which produced real latest prices with empty rolling features (the
    production 'dash-wall', credibility audit Finding A)."""
    from app.services.data_providers import stooq_provider

    rows, _warnings = stooq_provider.fetch_bars(ticker, ticker, start, end)
    dates_, closes_, volumes_, highs_, lows_ = [], [], [], [], []
    for r in rows:
        c = r.get("close")
        if not c or c <= 0:
            continue
        d = r["bar_date"] if "bar_date" in r else r.get("date")
        dates_.append(d if isinstance(d, date) else date.fromisoformat(str(d)[:10]))
        closes_.append(float(c))
        volumes_.append(int(r.get("volume") or 0))
        highs_.append(float(r.get("high") or c))
        lows_.append(float(r.get("low") or c))
    return Bars(dates_, closes_, volumes_, highs_, lows_)


def fetch_history(ticker: str, days: int) -> Bars:
    """Deepest-coverage-wins across yfinance -> stooq (K1)."""
    end = date.today()
    start = end - timedelta(days=days)
    need = _expected_sessions(days)

    yf_bars = Bars([], [], [], [], [])
    try:
        yf_bars = _fetch_history_yfinance(ticker, start, end)
    except Exception as exc:  # noqa: BLE001 — fall through to the next source
        _log.warning("fetch_history: yfinance failed for %s: %s", ticker, exc)
    if len(yf_bars.closes) >= need * MIN_COVERAGE and len(yf_bars.closes) >= 60:
        return yf_bars

    try:
        sq_bars = _bars_from_stooq(ticker, start, end)
    except Exception as exc:  # noqa: BLE001
        _log.warning("fetch_history: stooq failed for %s: %s", ticker, exc)
        sq_bars = Bars([], [], [], [], [])

    best = yf_bars if len(yf_bars.closes) >= len(sq_bars.closes) else sq_bars
    if len(yf_bars.closes) and best is sq_bars:
        _log.warning(
            "fetch_history: yfinance thin for %s (%d bars); stooq served %d",
            ticker, len(yf_bars.closes), len(sq_bars.closes),
        )
    if not best.closes:
        raise RuntimeError(
            f"no provider returned usable history for {ticker} in {start}..{end}"
        )
    return best


def _fetch_history_yfinance(ticker: str, start: date, end: date) -> Bars:
    tkr = yf.Ticker(ticker)
    df = tkr.history(
        start=start.isoformat(),
        end=(end + timedelta(days=1)).isoformat(),
        interval="1d",
        auto_adjust=False,
        actions=False,
    )
    if df is None or df.empty:
        raise RuntimeError(f"yfinance returned no data for {ticker}")
    dates_, closes_, volumes_, highs_, lows_ = [], [], [], [], []
    for ts, row in df.iterrows():
        d = ts.date() if hasattr(ts, "date") else ts
        try:
            c = float(row["Close"])
            v = int(row["Volume"])
            h = float(row["High"])
            lo = float(row["Low"])
        except (ValueError, TypeError):
            continue
        if c <= 0:
            continue
        dates_.append(d)
        closes_.append(c)
        volumes_.append(v)
        highs_.append(h)
        lows_.append(lo)
    return Bars(dates_, closes_, volumes_, highs_, lows_)




# ── News + sentiment ──────────────────────────────────────────────────────────

@dataclass
class NewsItem:
    title: str
    publisher: str
    published: str | None
    link: str
    sentiment_compound: float
    sentiment_label: str


_VADER = SentimentIntensityAnalyzer()


def _sentiment_label(score: float) -> str:
    if score >= 0.05:
        return "positive"
    if score <= -0.05:
        return "negative"
    return "neutral"


def fetch_news(ticker: str, limit: int = 20) -> tuple[list[NewsItem], bool]:
    """Pull ticker-specific news from yfinance + score with VADER.

    Returns (items, source_reachable). source_reachable is True if yfinance
    returned a valid (possibly empty) list; False if it raised.
    """
    try:
        raw = yf.Ticker(ticker).news or []
    except Exception:
        return [], False
    items: list[NewsItem] = []
    for entry in raw[:limit]:
        # yfinance has shipped multiple shapes; try both.
        content = entry.get("content") or entry
        title = (content.get("title") or "").strip()
        if not title:
            continue
        summary = (content.get("summary") or content.get("description") or "").strip()
        publisher = (
            (content.get("provider") or {}).get("displayName")
            or content.get("publisher")
            or "unknown"
        )
        link = content.get("canonicalUrl", {}).get("url") if isinstance(content.get("canonicalUrl"), dict) else None
        link = link or content.get("link") or ""
        published = content.get("pubDate") or content.get("displayTime")
        if not published and entry.get("providerPublishTime"):
            try:
                published = datetime.fromtimestamp(int(entry["providerPublishTime"]), tz=UTC).isoformat()
            except (ValueError, TypeError):
                published = None
        text = f"{title}. {summary}" if summary else title
        compound = _VADER.polarity_scores(text)["compound"]
        items.append(NewsItem(
            title=title,
            publisher=str(publisher),
            published=str(published) if published else None,
            link=str(link),
            sentiment_compound=round(compound, 4),
            sentiment_label=_sentiment_label(compound),
        ))
    return items, True


def news_within(items: list[NewsItem], days: int, anchor: date | None = None) -> list[NewsItem]:
    """Filter news items to ones published within `days` of `anchor`.

    When `anchor` is None we treat "now" as end-of-day today so news
    published earlier today is included. When `anchor` is a specific date
    (e.g. a backtest rebalance), we use midnight of that day to avoid
    look-ahead — only news strictly before that day counts.
    """
    if not items:
        return []
    if anchor is None:
        anchor_dt = datetime.now(UTC) + timedelta(minutes=1)
    else:
        anchor_dt = datetime(anchor.year, anchor.month, anchor.day, tzinfo=UTC)
    cutoff = anchor_dt - timedelta(days=days)
    out = []
    for it in items:
        if not it.published:
            continue
        try:
            pub = datetime.fromisoformat(it.published.replace("Z", "+00:00"))
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=UTC)
        except ValueError:
            continue
        if cutoff <= pub <= anchor_dt:
            out.append(it)
    return out




# ── Composite recommendation (mirrors DecisionPipelineService) ───────────────

# Profile-neutral defaults. The deployed pipeline applies caps/floors after
# this; we surface the raw composite so a human can judge.
STANCE_BUY_THRESHOLD = 0.30
STANCE_SELL_THRESHOLD = -0.25
# Translates a [-1, 1] composite into a target portfolio weight, capped at
# MAX_POSITION_WEIGHT from pipeline.py.
MAX_POSITION_WEIGHT = 0.15
MIN_POSITION_WEIGHT = 0.02


def composite_recommendation(engine_outputs: dict[str, dict]) -> dict:
    """Confidence-weighted blend of engine scores.

    Matches the spirit of DecisionPipelineService._aggregate_asset_signals:
    sum(score_i * confidence_i) / sum(confidence_i).
    """
    num = 0.0
    den = 0.0
    drivers: list[str] = []
    caveats: list[str] = []
    for key, out in engine_outputs.items():
        s = out.get("score", 0.0) or 0.0
        c = out.get("confidence", 0.0) or 0.0
        num += s * c
        den += c
        drivers.extend(f"[{key}] {d}" for d in out.get("drivers", []))
        caveats.extend(f"[{key}] {d}" for d in out.get("caveats", []))
    composite = round(num / den, 4) if den > 0 else 0.0
    avg_conf = round(den / len(engine_outputs), 3) if engine_outputs else 0.0

    if composite >= STANCE_BUY_THRESHOLD:
        stance = "buy"
    elif composite <= STANCE_SELL_THRESHOLD:
        stance = "sell"
    else:
        stance = "hold"

    # Map composite to a target weight (linear, capped). Cash if not buy.
    if stance == "buy":
        target_weight = min(MAX_POSITION_WEIGHT, max(MIN_POSITION_WEIGHT, composite * MAX_POSITION_WEIGHT))
    else:
        target_weight = 0.0

    return {
        "composite_score": composite,
        "stance": stance,
        "avg_confidence": avg_conf,
        "target_weight": round(target_weight, 4),
        "drivers": drivers[:10],
        "caveats": caveats[:10],
    }




# ── Multi-strategy walk-forward framework ────────────────────────────────────

# Each strategy is a pure (RebalanceState) -> target_position function.
# All strategies run on the SAME precomputed rebalance grid so feature
# computation happens once per date, not N×strategy times.


def sma(closes: list[float], n: int) -> float | None:
    if len(closes) < n:
        return None
    return sum(closes[-n:]) / n


def rsi(closes: list[float], n: int = 14) -> float | None:
    """Simple-average RSI over n periods (not Wilder-smoothed)."""
    if len(closes) < n + 1:
        return None
    gains, losses = 0.0, 0.0
    for i in range(-n, 0):
        diff = closes[i] - closes[i - 1]
        if diff > 0:
            gains += diff
        else:
            losses += -diff
    avg_gain = gains / n
    avg_loss = losses / n
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


@dataclass
class RebalanceState:
    date: date
    price: float
    features: dict
    engines: dict
    composite: dict
    window: Bars


@dataclass
class StrategyDef:
    key: str
    name: str
    category: str
    color: str
    description: str
    decide: object  # Callable[[RebalanceState], float] returning target position 0..1


def _generate_weekly_rebalances(start: date, end: date) -> list[date]:
    out = []
    d = start
    while d.weekday() != 0:  # Monday
        d += timedelta(days=1)
    while d <= end:
        out.append(d)
        d += timedelta(days=7)
    return out


def precompute_rebalance_states(
    bars: Bars,
    news_items: list[NewsItem],
    rebalances: list[date],
) -> list[RebalanceState]:
    """One pass: compute features/engines/composite per rebalance date.
    Strategies just read from this cache — no recomputation per strategy.
    """
    sorted_dates = bars.dates
    close_by_date = {d: c for d, c in zip(bars.dates, bars.closes, strict=False)}

    def close_at(d: date) -> float | None:
        lo, hi = 0, len(sorted_dates) - 1
        best = None
        while lo <= hi:
            mid = (lo + hi) // 2
            if sorted_dates[mid] <= d:
                best = sorted_dates[mid]
                lo = mid + 1
            else:
                hi = mid - 1
        return close_by_date.get(best) if best is not None else None

    states: list[RebalanceState] = []
    for reb in rebalances:
        price = close_at(reb)
        if price is None:
            continue
        window = bars.window_ending(reb)
        ticker_news = news_within(news_items, days=7, anchor=reb)
        feats = compute_features(
            window.closes, window.volumes,
            [n.sentiment_compound for n in ticker_news],
            news_source_exists=True,
        )
        engines = {k: fn(feats) for k, fn in ENGINE_FUNCTIONS.items()}
        comp = composite_recommendation(engines)
        states.append(RebalanceState(reb, price, feats, engines, comp, window))
    return states


def _compute_monthly_returns(equity_curve: list[dict]) -> dict[str, float]:
    """YYYY-MM -> percent return for the month (last value of month vs prev)."""
    by_month: dict[str, float] = {}
    for pt in equity_curve:
        d_str = pt["date"]
        d = datetime.fromisoformat(d_str).date() if isinstance(d_str, str) else d_str
        key = f"{d.year}-{d.month:02d}"
        by_month[key] = pt["value"]
    months = sorted(by_month.keys())
    out: dict[str, float] = {}
    prev = 100.0
    for m in months:
        v = by_month[m]
        out[m] = round((v / prev) - 1, 4) if prev > 0 else 0.0
        prev = v
    return out


def _returns_histogram(period_returns: list[float]) -> dict:
    """Bin weekly returns into fixed buckets for distribution visualisation."""
    bins = [-0.10, -0.05, -0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03, 0.05, 0.10]
    counts = [0] * (len(bins) - 1)
    for r in period_returns:
        if r < bins[0]:
            counts[0] += 1
            continue
        if r >= bins[-1]:
            counts[-1] += 1
            continue
        for k in range(len(bins) - 1):
            if bins[k] <= r < bins[k + 1]:
                counts[k] += 1
                break
    return {"bins": bins, "counts": counts}


def run_strategy(
    states: list[RebalanceState],
    strategy: StrategyDef,
    cost_bps: int = 10,
    rolling_window: int = 4,
) -> dict:
    """Run one strategy over precomputed states. Returns rich metrics + curves."""
    if not states:
        return {"key": strategy.key, "name": strategy.name, "metrics": {}, "equity_curve": []}

    equity = 100.0
    peak = 100.0
    max_dd = 0.0
    current_pos = 0.0
    last_price: float | None = None
    trades = 0
    long_count = 0
    equity_curve = []
    drawdown_curve = []
    period_returns_list = []

    for st in states:
        if last_price is not None:
            bar_return = (st.price - last_price) / last_price
            pr = current_pos * bar_return
            equity *= (1 + pr)
            period_returns_list.append({"date": st.date.isoformat(), "return": round(pr, 6)})
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd
            drawdown_curve.append({"date": st.date.isoformat(), "value": round(-dd, 4)})
        else:
            drawdown_curve.append({"date": st.date.isoformat(), "value": 0.0})

        target = float(strategy.decide(st))
        target = max(0.0, min(1.0, target))
        if target != current_pos:
            cost = abs(target - current_pos) * cost_bps / 10000
            equity *= (1 - cost)
            trades += 1
            current_pos = target

        if current_pos > 0:
            long_count += 1

        equity_curve.append({
            "date": st.date.isoformat(),
            "value": round(equity, 2),
            "position": current_pos,
        })
        last_price = st.price

    # Aggregate metrics
    days = (states[-1].date - states[0].date).days
    total_return = (equity / 100.0) - 1
    annualized = (1 + total_return) ** (365 / max(days, 1)) - 1 if days > 30 else None
    period_returns = [p["return"] for p in period_returns_list]
    vol = sharpe = win_rate = None
    if len(period_returns) >= 2:
        mean_r = sum(period_returns) / len(period_returns)
        var = sum((r - mean_r) ** 2 for r in period_returns) / len(period_returns)
        period_std = math.sqrt(var)
        vol = period_std * math.sqrt(52)
        if vol > 0:
            sharpe = (mean_r * 52) / vol
        win_rate = sum(1 for r in period_returns if r > 0) / len(period_returns)

    # Rolling Sharpe (window of `rolling_window` periods ≈ 30 calendar days for w=4).
    rolling_sharpe = []
    for i, pr in enumerate(period_returns_list):
        if i + 1 < rolling_window:
            rolling_sharpe.append({"date": pr["date"], "value": None})
            continue
        win_pr = [period_returns_list[j]["return"] for j in range(i + 1 - rolling_window, i + 1)]
        m = sum(win_pr) / rolling_window
        v = math.sqrt(sum((r - m) ** 2 for r in win_pr) / rolling_window)
        if v > 0:
            rs_val = (m * 52) / (v * math.sqrt(52))
            rolling_sharpe.append({"date": pr["date"], "value": round(rs_val, 2)})
        else:
            rolling_sharpe.append({"date": pr["date"], "value": None})

    monthly_returns = _compute_monthly_returns(equity_curve)
    histogram = _returns_histogram(period_returns)

    calmar = None
    if annualized is not None and max_dd > 0:
        calmar = round(annualized / max_dd, 2)

    return {
        "key": strategy.key,
        "name": strategy.name,
        "category": strategy.category,
        "color": strategy.color,
        "description": strategy.description,
        "metrics": {
            "total_return": round(total_return, 4),
            "annualized_return": round(annualized, 4) if annualized is not None else None,
            "max_drawdown": round(-max_dd, 4),
            "sharpe_ratio": round(sharpe, 2) if sharpe is not None else None,
            "volatility": round(vol, 4) if vol is not None else None,
            "win_rate": round(win_rate, 3) if win_rate is not None else None,
            "long_share": round(long_count / len(states), 3),
            "trades": trades,
            "calmar_ratio": calmar,
        },
        "equity_curve": equity_curve,
        "drawdown_curve": drawdown_curve,
        "period_returns": period_returns_list,
        "rolling_sharpe": rolling_sharpe,
        "monthly_returns": monthly_returns,
        "returns_histogram": histogram,
    }


# ── Strategy decision functions ──────────────────────────────────────────────

def _decide_composite(threshold: float):
    def fn(st: RebalanceState) -> float:
        return 1.0 if st.composite["composite_score"] >= threshold else 0.0
    return fn


def _decide_engine(engine_key: str, threshold: float = 0.30):
    def fn(st: RebalanceState) -> float:
        sc = st.engines.get(engine_key, {}).get("score", 0.0) or 0.0
        return 1.0 if sc >= threshold else 0.0
    return fn


def _decide_sma_crossover(fast: int = 20, slow: int = 50):
    def fn(st: RebalanceState) -> float:
        closes = st.window.closes
        f = sma(closes, fast)
        s = sma(closes, slow)
        if f is None or s is None:
            return 0.0
        return 1.0 if f > s else 0.0
    return fn


def _decide_rsi_mean_reversion(low: float = 30, high: float = 70):
    """Stateful: enter long when RSI<low, exit when RSI>high, otherwise hold prior position."""
    state = {"pos": 0.0}
    def fn(st: RebalanceState) -> float:
        r = rsi(st.window.closes, 14)
        if r is None:
            return state["pos"]
        if r < low:
            state["pos"] = 1.0
        elif r > high:
            state["pos"] = 0.0
        return state["pos"]
    return fn


def _decide_buy_and_hold(st: RebalanceState) -> float:
    return 1.0


def build_main_strategies() -> list[StrategyDef]:
    return [
        StrategyDef("composite_010", "Composite ≥ 0.10", "FINRLX ensemble", "#38bdf8",
                    "Live FINRLX scoring: long when confidence-weighted engine blend ≥ 0.10.",
                    _decide_composite(0.10)),
        StrategyDef("tech_only", "Tech-momentum only", "Single engine", "#22c55e",
                    "Long when technical_momentum engine score ≥ 0.30.",
                    _decide_engine("technical_momentum", 0.30)),
        StrategyDef("risk_only", "Risk-quality only", "Single engine", "#a78bfa",
                    "Long when risk_quality engine score ≥ 0.30 (low vol + shallow DD).",
                    _decide_engine("risk_quality", 0.30)),
        StrategyDef("news_only", "News-sentiment only", "Single engine", "#fbbf24",
                    "Long when news_sentiment engine score ≥ 0.30.",
                    _decide_engine("news_sentiment", 0.30)),
        StrategyDef("sma_xover", "SMA(20/50) crossover", "Classical TA", "#f472b6",
                    "Long when 20-day SMA > 50-day SMA (trend following).",
                    _decide_sma_crossover(20, 50)),
        StrategyDef("rsi_mr", "RSI(14) mean-reversion", "Classical TA", "#fb923c",
                    "Long on RSI<30 (oversold), exit on RSI>70 (overbought), hold otherwise.",
                    _decide_rsi_mean_reversion(30, 70)),
        StrategyDef("buy_hold", "Buy & Hold", "Benchmark", "#94a3b8",
                    "Always long — passive benchmark.",
                    _decide_buy_and_hold),
    ]


def build_threshold_sweep() -> list[StrategyDef]:
    return [
        StrategyDef("comp_005", "Composite ≥ 0.05", "Threshold sweep", "#67e8f9",
                    "Loose gate (composite ≥ 0.05).", _decide_composite(0.05)),
        StrategyDef("comp_010", "Composite ≥ 0.10", "Threshold sweep", "#38bdf8",
                    "Default gate (composite ≥ 0.10).", _decide_composite(0.10)),
        StrategyDef("comp_020", "Composite ≥ 0.20", "Threshold sweep", "#0ea5e9",
                    "Tighter gate (composite ≥ 0.20).", _decide_composite(0.20)),
        StrategyDef("comp_030", "Composite ≥ 0.30", "Threshold sweep", "#0369a1",
                    "Strict gate (composite ≥ 0.30).", _decide_composite(0.30)),
    ]


def collect_feature_evolution(states: list[RebalanceState]) -> dict:
    """Time series of features across the backtest window."""
    keys = ["return_5d", "return_20d", "return_60d", "volatility_20d",
            "drawdown_20d", "relative_volume_20d", "news_sentiment_7d"]
    out: dict = {"dates": [st.date.isoformat() for st in states]}
    for k in keys:
        out[k] = [st.features.get(k, (None, None))[0] for st in states]
    out["composite_score"] = [st.composite["composite_score"] for st in states]
    return out


def collect_decision_trace(states: list[RebalanceState]) -> dict:
    """Per-rebalance vote of each engine + the composite, for the trace chart."""
    stance_val = {"buy": 1, "hold": 0, "sell": -1, "trim": -0.5}
    return {
        "dates": [st.date.isoformat() for st in states],
        "price": [st.price for st in states],
        "technical_momentum": [stance_val.get(st.engines["technical_momentum"]["stance"], 0) for st in states],
        "risk_quality": [stance_val.get(st.engines["risk_quality"]["stance"], 0) for st in states],
        "news_sentiment": [stance_val.get(st.engines["news_sentiment"]["stance"], 0) for st in states],
        "composite_stance": [stance_val.get(st.composite["stance"], 0) for st in states],
        "composite_score": [st.composite["composite_score"] for st in states],
    }




# ── HTML report (Chart.js via CDN) ───────────────────────────────────────────
#
# The template uses [[TOKEN]] placeholders (not {token}) so CSS/JS braces don't
# need escaping. Tokens are substituted by str.replace in build_html_report.

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>FINRLX Analysis · [[TICKER]]</title>
[[CHARTJS_SCRIPT]]
<style>
  :root {
    --bg: #0f172a; --panel: #1e293b; --panel2: #0b1224; --text: #e2e8f0;
    --muted: #94a3b8; --border: #334155;
    --buy: #16a34a; --sell: #dc2626; --hold: #6b7280;
    --pos: #22c55e; --neg: #ef4444; --neu: #94a3b8;
    --accent: #38bdf8;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; background: var(--bg); color: var(--text);
    font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
  .wrap { max-width: 1400px; margin: 0 auto; padding: 28px 24px 80px; }
  header { display: flex; align-items: center; gap: 24px; padding: 28px;
    background: linear-gradient(135deg, #1e3a8a 0%, #1e293b 100%); border-radius: 16px;
    margin-bottom: 32px; border: 1px solid var(--border); }
  header h1 { margin: 0; font-size: 30px; letter-spacing: -0.5px; }
  header .meta { color: var(--muted); margin-top: 6px; font-size: 14px; }
  .stance { padding: 8px 16px; border-radius: 999px; font-weight: 700; font-size: 14px;
    letter-spacing: 1px; color: white; }
  .stance.BUY { background: var(--buy); }
  .stance.SELL { background: var(--sell); }
  .stance.HOLD { background: var(--hold); }
  .stance.TRIM { background: #f59e0b; }
  .verdict-line { display: flex; align-items: center; gap: 28px; margin-top: 12px; flex-wrap: wrap; }
  .verdict-line .num { font-size: 28px; font-weight: 700; }
  .verdict-line .label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
  .section-title { font-size: 13px; text-transform: uppercase; letter-spacing: 1.5px;
    color: var(--accent); margin: 36px 0 14px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
  .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 20px; }
  .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 20px; }
  .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
  .card { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
  .card h2 { margin: 0 0 16px; font-size: 15px; font-weight: 600; color: var(--text);
    text-transform: uppercase; letter-spacing: 0.5px; }
  .card h2 .sub { color: var(--muted); font-weight: 400; font-size: 12px; text-transform: none; }
  .card.full { grid-column: 1 / -1; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 8px 6px; border-bottom: 1px solid var(--border); }
  th { color: var(--muted); font-weight: 500; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
  td.num { text-align: right; font-variant-numeric: tabular-nums; }
  .pill { display: inline-block; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 600; }
  .pill.pos { background: rgba(34, 197, 94, 0.15); color: var(--pos); }
  .pill.neg { background: rgba(239, 68, 68, 0.15); color: var(--neg); }
  .pill.neu { background: rgba(148, 163, 184, 0.15); color: var(--neu); }
  .swatch { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; vertical-align: middle; }
  .driver { padding: 4px 0; font-size: 13px; color: var(--text); }
  .driver::before { content: "▸"; color: var(--accent); margin-right: 8px; }
  .caveat { padding: 4px 0; font-size: 13px; color: #fca5a5; }
  .caveat::before { content: "⚠"; margin-right: 8px; }
  .news-item { padding: 10px 0; border-bottom: 1px solid var(--border); font-size: 13px; }
  .news-item:last-child { border-bottom: none; }
  .news-item .title { font-weight: 500; margin-bottom: 4px; }
  .news-item .title a { color: var(--text); text-decoration: none; }
  .news-item .title a:hover { color: var(--accent); text-decoration: underline; }
  .news-item .src { color: var(--muted); font-size: 12px; }
  .footnote { color: var(--muted); font-size: 12px; margin-top: 24px; padding: 16px;
    background: var(--panel2); border-radius: 8px; border-left: 3px solid var(--accent); }
  canvas { max-height: 320px; }
  canvas.mini { max-height: 160px; }
  canvas.tall { max-height: 380px; }
  .composite-bar { position: relative; height: 24px; background: var(--panel2);
    border-radius: 12px; overflow: hidden; margin: 8px 0; }
  .composite-bar .fill { position: absolute; top: 0; bottom: 0; }
  .composite-bar .mid { position: absolute; top: 0; bottom: 0; left: 50%; width: 1px;
    background: var(--muted); opacity: 0.5; }
  .scale { display: flex; justify-content: space-between; color: var(--muted); font-size: 11px; }
  .heatmap { width: 100%; border-collapse: separate; border-spacing: 2px; font-size: 12px;
    font-variant-numeric: tabular-nums; }
  .heatmap th { padding: 6px 4px; color: var(--muted); font-weight: 500; text-align: center;
    text-transform: uppercase; letter-spacing: 0.5px; border: none; }
  .heatmap td { padding: 8px 4px; text-align: center; border-radius: 4px; border: none;
    color: var(--text); font-weight: 500; }
  .heatmap td.empty { background: var(--panel2); color: var(--muted); }
  .heatmap th.year-label { text-align: right; padding-right: 10px; }
  .compare-table tr.best td { color: var(--pos); }
  .compare-table tr.bh td { color: #fbbf24; }
  .compare-table tr:hover { background: rgba(56, 189, 248, 0.05); }
  .strat-name { display: flex; align-items: center; gap: 8px; }
  .category-tag { color: var(--muted); font-size: 11px; }
  .legend-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 6px; margin-top: 10px; font-size: 12px; color: var(--muted); }

  /* ============================================================
     RESPONSIVE — additive. Desktop above 900px is unchanged.
     Two breakpoints: 900px (tablet/landscape), 640px (phone).
     ============================================================ */

  @media (max-width: 900px) {
    .wrap { padding: 20px 16px 60px; }
    .grid-3 { grid-template-columns: repeat(2, 1fr); }
    .grid-4 { grid-template-columns: repeat(2, 1fr); }
    header { padding: 22px; gap: 16px; }
    header h1 { font-size: 24px; }
    .verdict-line { gap: 20px; }
    .verdict-line .num { font-size: 24px; }
    canvas { max-height: 280px; }
    canvas.tall { max-height: 340px; }
  }

  @media (max-width: 640px) {
    .wrap { padding: 14px 12px 48px; }

    /* Header: stack vertically, shrink type, tap-friendly stance pill */
    header {
      flex-direction: column;
      align-items: flex-start;
      padding: 18px 16px;
      gap: 10px;
      margin-bottom: 22px;
      border-radius: 12px;
    }
    header h1 { font-size: 20px; line-height: 1.25; }
    header .meta { font-size: 12px; }
    .stance {
      padding: 10px 18px; font-size: 13px; min-height: 44px;
      display: inline-flex; align-items: center;
    }
    .verdict-line { gap: 14px 20px; margin-top: 8px; }
    .verdict-line .num { font-size: 20px; }
    .verdict-line .label { font-size: 11px; }

    /* Section titles + cards */
    .section-title { font-size: 12px; margin: 24px 0 10px; }
    .grid, .grid-3, .grid-4 { grid-template-columns: 1fr; gap: 14px; margin-bottom: 14px; }
    .card { padding: 14px; border-radius: 10px; }
    .card h2 { font-size: 13px; margin-bottom: 12px; }
    .card h2 .sub { display: block; margin-top: 2px; font-size: 11px; }

    /* Chart heights — Chart.js handles width, we cap height per device */
    canvas { max-height: 240px !important; }
    canvas.mini { max-height: 140px !important; }
    canvas.tall { max-height: 280px !important; }

    /* Wide tables (strategy comparison, threshold sweep, monthly heatmap):
       turn the <table> itself into a horizontal-scroll container with a
       sticky first column so the row identity stays in view as you swipe. */
    .card.full > table.compare-table,
    .card > table.heatmap {
      display: block;
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
      white-space: nowrap;
      max-width: 100%;
    }
    .compare-table th, .compare-table td { padding: 10px 8px; font-size: 12px; }
    .compare-table th:first-child,
    .compare-table td:first-child {
      position: sticky; left: 0; z-index: 2;
      background: var(--panel);
      box-shadow: 1px 0 0 var(--border);
      min-width: 140px;
    }
    /* Don't let the row-state colour bleed onto the sticky first cell */
    .compare-table tr.best td:first-child,
    .compare-table tr.bh   td:first-child { background: var(--panel); }

    .heatmap { font-size: 11px; }
    .heatmap th, .heatmap td { padding: 6px 3px; min-width: 38px; }
    .heatmap th:first-child,
    .heatmap td:first-child {
      position: sticky; left: 0; z-index: 2;
      background: var(--panel);
      box-shadow: 1px 0 0 var(--border);
    }

    /* Features table (snapshot, 3 cols) doesn't need scroll, just tighter cells */
    .card table { font-size: 12px; }
    .card table th, .card table td { padding: 8px 4px; }

    /* News list: ≥44px tap targets per Apple HIG */
    .news-item { padding: 14px 0; font-size: 13px; }
    .news-item .title { font-size: 14px; line-height: 1.35; margin-bottom: 6px; }
    .news-item .title a { display: inline-block; min-height: 44px; padding: 2px 0;
                          overflow-wrap: break-word; word-break: break-word; }
    .news-item .src { font-size: 11px; }
    .pill { padding: 4px 10px; font-size: 11px; }

    /* Footnote, composite bar, legend */
    .footnote { font-size: 11px; padding: 14px; line-height: 1.5; }
    .composite-bar { height: 20px; }
    .scale { font-size: 10px; }
    .legend-grid { grid-template-columns: 1fr 1fr; font-size: 11px; }
  }

  /* iPhone SE / Pixel 4a class (≤380px) */
  @media (max-width: 380px) {
    header h1 { font-size: 18px; }
    .verdict-line .num { font-size: 18px; }
    .wrap { padding: 12px 10px 40px; }
  }

  /* ============================================================
     OVERFLOW CONTAINMENT — stops Chart.js canvases from
     escaping their cards on mobile. The `min-width: 0` rules on
     grids/cards are the critical part: CSS grid items default
     to `min-width: auto` (= content size), so a wide canvas
     would force the grid track to grow and blow out the page
     horizontally. Setting min-width:0 lets cards shrink.
     ============================================================ */
  * { -webkit-tap-highlight-color: transparent; }
  html, body { overflow-x: hidden; max-width: 100%; }
  .wrap { overflow-x: hidden; }
  .grid, .grid-3, .grid-4 { min-width: 0; }
  .card { min-width: 0; overflow: hidden; }
  canvas { max-width: 100%; height: auto; display: block; touch-action: pan-y; }

  /* Sentiment donut needs a square container — wrapping a square
     parent keeps it round when maintainAspectRatio is off. */
  .donut-wrap { position: relative; width: 100%; max-width: 260px;
    aspect-ratio: 1 / 1; margin: 0 auto; }
  .donut-wrap canvas { max-height: none; }

  /* Sparse-data empty state for mini feature-evolution charts.
     Diagonal hatch reads as "intentionally empty" rather than
     "broken / loading". Used when a series is >70% null. */
  .mini-empty { display: flex; flex-direction: column; justify-content: center;
    align-items: flex-start; min-height: 140px; padding: 14px;
    border-radius: 10px;
    background: repeating-linear-gradient(45deg,
      rgba(148,163,184,.04) 0 6px, transparent 6px 12px);
    border: 1px dashed rgba(148,163,184,.25); }
  .mini-empty__icon { width: 22px; height: 22px; border-radius: 50%;
    background: rgba(251,191,36,.18); color: #fbbf24; font-weight: 700;
    display: grid; place-items: center; font-size: 13px; margin-bottom: 6px; }
  .mini-empty__title { font-size: 12px; font-weight: 600; color: var(--text); }
  .mini-empty__body { font-size: 11px; line-height: 1.4; color: var(--muted);
    margin-top: 4px; }
  .mini-empty__meta { font-size: 10px; color: var(--muted); opacity: .7;
    margin-top: 6px; }
  .chart-note { font-size: 11px; color: var(--muted); margin-top: 8px;
    line-height: 1.4; font-style: italic; }

  /* On phones, bump decision-trace + equity .tall a touch and constrain
     the legend so it doesn't squeeze the plot area to zero. */
  @media (max-width: 640px) {
    canvas.tall { max-height: 320px !important; }
  }
</style>
</head>
<body>
<div class="wrap">

  <header>
    <div style="flex: 1">
      <h1>[[TICKER]] · FINRLX Multi-Strategy Analysis</h1>
      <div class="meta">As-of [[AS_OF]] · Last close $[[LAST_CLOSE]] · [[NBARS]] bars · Generated [[GENERATED]]</div>
      <div class="verdict-line">
        <span class="stance [[STANCE]]">[[STANCE]]</span>
        <div><div class="num">[[COMPOSITE]]</div><div class="label">composite score</div></div>
        <div><div class="num">[[WEIGHT]]</div><div class="label">suggested weight</div></div>
        <div><div class="num">[[AVG_CONF]]</div><div class="label">avg confidence</div></div>
        <div><div class="num">[[N_STRATS]]</div><div class="label">strategies compared</div></div>
      </div>
    </div>
  </header>

  <!-- ────────────  SNAPSHOT  ──────────── -->
  <div class="section-title">1 · Snapshot</div>

  <div class="grid-3">
    <div class="card">
      <h2>Composite <span class="sub">weight-centric</span></h2>
      <div class="composite-bar">
        <div class="mid"></div>
        <div class="fill" style="background: [[COMPOSITE_COLOR]]; left: [[COMPOSITE_LEFT]]%; width: [[COMPOSITE_WIDTH]]%;"></div>
      </div>
      <div class="scale"><span>-1.00 SELL</span><span>0</span><span>BUY +1.00</span></div>
      <div style="margin-top: 16px;">
        <div style="color: var(--muted); font-size: 12px; margin-bottom: 8px;">DRIVERS</div>
        [[DRIVERS_HTML]]
        <div style="color: var(--muted); font-size: 12px; margin: 12px 0 8px;">CAVEATS</div>
        [[CAVEATS_HTML]]
      </div>
    </div>

    <div class="card">
      <h2>Engine ensemble <span class="sub">live FINRLX scoring</span></h2>
      <canvas id="engineChart"></canvas>
    </div>

    <div class="card">
      <h2>News sentiment <span class="sub">last 7 days</span></h2>
      <div class="donut-wrap"><canvas id="sentimentDonut"></canvas></div>
    </div>
  </div>

  <div class="grid">
    <div class="card">
      <h2>Price <span class="sub">backtest window</span></h2>
      <canvas id="priceChart"></canvas>
    </div>
    <div class="card">
      <h2>Features <span class="sub">FINRLX feature layer</span></h2>
      <table>
        <thead><tr><th>feature</th><th style="text-align:right">value</th><th>quality</th></tr></thead>
        <tbody>
          [[FEATURES_ROWS]]
        </tbody>
      </table>
    </div>
  </div>

  <!-- ────────────  STRATEGY COMPARISON  ──────────── -->
  <div class="section-title">2 · Strategy comparison · walk-forward weekly, cost 10 bps</div>

  <div class="card full">
    <h2>Equity curves <span class="sub">base 100 · click legend to toggle</span></h2>
    <canvas id="equityOverlay" class="tall"></canvas>
  </div>

  <div class="card full" style="margin-top: 20px;">
    <h2>Comparison table <span class="sub">sorted by Sharpe · buy &amp; hold pinned</span></h2>
    <table class="compare-table">
      <thead><tr>
        <th>strategy</th><th>category</th>
        <th class="num">total return</th><th class="num">annualized</th>
        <th class="num">max DD</th><th class="num">Sharpe</th><th class="num">Calmar</th>
        <th class="num">volatility</th><th class="num">win rate</th>
        <th class="num">long %</th><th class="num">trades</th>
      </tr></thead>
      <tbody>
        [[STRATEGY_TABLE_ROWS]]
      </tbody>
    </table>
  </div>

  <div class="card full" style="margin-top: 20px;">
    <h2>Composite threshold sweep <span class="sub">gate sensitivity</span></h2>
    <table class="compare-table">
      <thead><tr>
        <th>threshold</th>
        <th class="num">total return</th><th class="num">annualized</th>
        <th class="num">max DD</th><th class="num">Sharpe</th><th class="num">Calmar</th>
        <th class="num">long %</th><th class="num">trades</th>
      </tr></thead>
      <tbody>
        [[SWEEP_TABLE_ROWS]]
      </tbody>
    </table>
  </div>

  <!-- ────────────  BACKTEST ANALYTICS  ──────────── -->
  <div class="section-title">3 · Backtest analytics</div>

  <div class="grid">
    <div class="card">
      <h2>Drawdown timeline <span class="sub">underwater plot · all strategies</span></h2>
      <canvas id="drawdownChart"></canvas>
    </div>
    <div class="card">
      <h2>Rolling 30d Sharpe <span class="sub">4-week window</span></h2>
      <canvas id="rollingSharpeChart"></canvas>
    </div>
  </div>

  <div class="grid">
    <div class="card">
      <h2>Weekly returns distribution <span class="sub">composite ≥ 0.10 vs buy &amp; hold</span></h2>
      <canvas id="returnsHist"></canvas>
    </div>
    <div class="card">
      <h2>Monthly returns heatmap <span class="sub">composite ≥ 0.10 strategy</span></h2>
      [[MONTHLY_HEATMAP_HTML]]
    </div>
  </div>

  <!-- ────────────  DECISION TRACE  ──────────── -->
  <div class="section-title">4 · Decision trace · how engines voted over time</div>

  <div class="card full">
    <h2>Engine votes vs price <span class="sub">1 = buy · 0 = hold · -1 = sell · -0.5 = trim</span></h2>
    <canvas id="decisionTrace" class="tall"></canvas>
  </div>

  <!-- ────────────  FEATURE EVOLUTION  ──────────── -->
  <div class="section-title">5 · Feature evolution · is the current BUY on typical or extreme readings?</div>

  <div class="grid-4">
    <div class="card">
      <h2>20-day return <span class="sub">momentum</span></h2>
      <canvas id="featRet20" class="mini"></canvas>
    </div>
    <div class="card">
      <h2>20-day volatility (ann) <span class="sub">risk</span></h2>
      <canvas id="featVol20" class="mini"></canvas>
    </div>
    <div class="card">
      <h2>7-day news sentiment <span class="sub">VADER</span></h2>
      <canvas id="featSent" class="mini"></canvas>
    </div>
    <div class="card">
      <h2>Composite score <span class="sub">weight-centric blend</span></h2>
      <canvas id="featComposite" class="mini"></canvas>
    </div>
  </div>

  <!-- ────────────  NEWS  ──────────── -->
  <div class="section-title">6 · Recent news · ticker-specific · VADER sentiment</div>

  <div class="card full">
    <div>[[NEWS_HTML]]</div>
  </div>

  <div class="footnote">
    <strong>Note on RL and methodology:</strong> All [[N_STRATS]] strategies above are deterministic
    decision rules run on the same walk-forward weekly grid with identical 10 bps transaction cost.
    The FINRLX engine ensemble (technical_momentum, risk_quality, news_sentiment) is the live
    production scoring layer. The FinRL-X RL trainer in this repo (rl_adapter.py) is
    research/offline-only and gated by safety flags — no trained RL policies exist in the codebase,
    so none are included in this comparison. SMA crossover and RSI mean-reversion are classical
    TA baselines for comparison. Backtests use no look-ahead: features at each rebalance read only
    bars with date ≤ rebalance date. News sentiment uses ticker news available up to the rebalance
    date. Past performance does not predict future returns. This is single-ticker analysis only —
    portfolio-level allocation, profile overrides, and risk overlays are applied later by
    DecisionPipelineService.
    <br><br>
    <strong>News-history limitation:</strong> historical news sentiment is reconstructable only for
    the most recent rebalances — yfinance exposes roughly the last 7-30 days of headlines, so
    past-week sentiment for older rebalances simply isn't available. Strategies that depend solely
    on this signal correspondingly show sparse rolling-window metrics. This is a data-source
    limitation, not a computation error.
  </div>
</div>

<script id="report-data" type="application/json">[[DATA_JSON]]</script>
<script>
  const DATA = JSON.parse(document.getElementById('report-data').textContent);
  const muted = "#94a3b8", text = "#e2e8f0", border = "#334155";
  Chart.defaults.color = text;
  Chart.defaults.borderColor = border;
  Chart.defaults.font.family = '-apple-system, "Segoe UI", Roboto, sans-serif';
  // Mobile fix: turning OFF maintainAspectRatio means each canvas fills its
  // parent's width and respects the CSS-set max-height — the cause of the
  // "graphs overflow the screen" symptom on iPhone. Capping devicePixelRatio
  // at 2 prevents 9 MB backing buffers on 3x iPhone Pro displays.
  Chart.defaults.maintainAspectRatio = false;
  Chart.defaults.devicePixelRatio = Math.min(window.devicePixelRatio || 1, 2);

  // ─── Engine ensemble (horizontal bars) ───
  const engKeys = Object.keys(DATA.engines);
  new Chart(document.getElementById('engineChart'), {
    type: 'bar',
    data: {
      labels: engKeys,
      datasets: [{
        label: 'score',
        data: engKeys.map(k => DATA.engines[k].score),
        backgroundColor: engKeys.map(k => {
          const s = DATA.engines[k].score;
          return s >= 0.3 ? '#16a34a' : s <= -0.25 ? '#dc2626' : '#6b7280';
        }),
        borderRadius: 6,
      }]
    },
    options: {
      indexAxis: 'y', responsive: true,
      scales: { x: { min: -1, max: 1 }, y: { grid: { display: false } } },
      plugins: { legend: { display: false } }
    }
  });

  // ─── Sentiment donut ───
  const sSum = DATA.sentiment_summary;
  new Chart(document.getElementById('sentimentDonut'), {
    type: 'doughnut',
    data: {
      labels: ['Positive', 'Neutral', 'Negative'],
      datasets: [{
        data: [sSum.positive, sSum.neutral, sSum.negative],
        backgroundColor: ['#22c55e', '#94a3b8', '#ef4444'],
        borderColor: '#1e293b', borderWidth: 2,
      }]
    },
    options: {
      responsive: true, cutout: '60%',
      plugins: {
        legend: { position: 'bottom' },
        title: { display: true, text: sSum.total + ' articles · mean compound ' + sSum.mean_compound }
      }
    }
  });

  // ─── Price chart ───
  const pricePts = DATA.price_curve;
  new Chart(document.getElementById('priceChart'), {
    type: 'line',
    data: {
      labels: pricePts.map(p => p.date),
      datasets: [{
        label: 'Close', data: pricePts.map(p => p.close),
        borderColor: '#38bdf8', backgroundColor: 'rgba(56, 189, 248, 0.1)',
        fill: true, tension: 0.2, pointRadius: 0, borderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      interaction: { intersect: false, mode: 'index' },
      scales: { x: { ticks: { maxTicksLimit: 8 } } },
      plugins: { legend: { display: false } }
    }
  });

  // ─── Strategy equity overlay ───
  function strategyLines(strategies, valueAccessor, opts) {
    opts = opts || {};
    return strategies.map(s => ({
      label: s.name,
      data: (s[opts.curveKey || 'equity_curve']).map(valueAccessor),
      borderColor: s.color,
      borderDash: s.key === 'buy_hold' ? [5, 5] : undefined,
      backgroundColor: 'transparent',
      tension: 0.1, pointRadius: 0, borderWidth: 2,
    }));
  }
  const sampleLabels = DATA.strategies[0].equity_curve.map(p => p.date);
  new Chart(document.getElementById('equityOverlay'), {
    type: 'line',
    data: {
      labels: sampleLabels,
      datasets: strategyLines(DATA.strategies, p => p.value, {})
    },
    options: {
      responsive: true,
      interaction: { intersect: false, mode: 'index' },
      scales: { x: { ticks: { maxTicksLimit: 10 } } },
      plugins: { legend: { position: 'bottom', labels: { padding: 14, font: { size: 11 } } } }
    }
  });

  // ─── Drawdown timeline ───
  new Chart(document.getElementById('drawdownChart'), {
    type: 'line',
    data: {
      labels: DATA.strategies[0].drawdown_curve.map(p => p.date),
      datasets: strategyLines(DATA.strategies, p => (p.value || 0) * 100, { curveKey: 'drawdown_curve' })
    },
    options: {
      responsive: true,
      interaction: { intersect: false, mode: 'index' },
      scales: {
        x: { ticks: { maxTicksLimit: 10 } },
        y: { title: { display: true, text: 'Drawdown %' } }
      },
      plugins: { legend: { position: 'bottom', labels: { padding: 10, font: { size: 11 } } } }
    }
  });

  // ─── Rolling Sharpe ───
  // Drop strategies whose interior rolling Sharpe is >70% null — they're
  // cash most of the time, so rolling std-dev is zero and the line becomes
  // a dashed scribble that doesn't help the comparison. A note below the
  // chart names them so the reader knows nothing was hidden silently.
  const SPARSE_SHARPE_NULL_THRESHOLD = 0.70;
  function rsNullFractionInterior(s) {
    const interior = s.rolling_sharpe.slice(4);  // skip the 4-week warm-up
    if (!interior.length) return 1;
    let n = 0;
    for (const p of interior) if (p.value === null || p.value === undefined) n++;
    return n / interior.length;
  }
  const rsKept = [], rsDropped = [];
  for (const s of DATA.strategies) {
    if (s.key === 'buy_hold') { rsKept.push(s); continue; }
    if (rsNullFractionInterior(s) > SPARSE_SHARPE_NULL_THRESHOLD) rsDropped.push(s);
    else rsKept.push(s);
  }
  new Chart(document.getElementById('rollingSharpeChart'), {
    type: 'line',
    data: {
      labels: DATA.strategies[0].rolling_sharpe.map(p => p.date),
      datasets: rsKept.map(s => ({
        label: s.name,
        data: s.rolling_sharpe.map(p => p.value),
        borderColor: s.color,
        borderDash: s.key === 'buy_hold' ? [5, 5] : undefined,
        backgroundColor: 'transparent',
        tension: 0.1, pointRadius: 0, borderWidth: 2, spanGaps: false,
      }))
    },
    options: {
      interaction: { intersect: false, mode: 'index' },
      scales: {
        x: { ticks: { maxTicksLimit: 10 } },
        y: { title: { display: true, text: 'Rolling Sharpe (annualized)' } }
      },
      plugins: { legend: { position: 'bottom', labels: { padding: 10, font: { size: 11 } } } }
    }
  });
  if (rsDropped.length) {
    const note = document.createElement('div');
    note.className = 'chart-note';
    note.textContent = 'Omitted: ' + rsDropped.map(s => s.name).join(', ')
      + ' — these strategies hold cash most weeks, so rolling std-dev is undefined.'
      + ' See the equity-curve chart above for their performance.';
    document.getElementById('rollingSharpeChart').after(note);
  }

  // ─── Returns histogram ───
  const compStrat = DATA.strategies.find(s => s.key === 'composite_010') || DATA.strategies[0];
  const bhStrat = DATA.strategies.find(s => s.key === 'buy_hold') || DATA.strategies[0];
  const histBins = compStrat.returns_histogram.bins;
  const histLabels = [];
  for (let i = 0; i < histBins.length - 1; i++) {
    const lo = (histBins[i] * 100).toFixed(0);
    const hi = (histBins[i+1] * 100).toFixed(0);
    histLabels.push(lo + ' to ' + hi + '%');
  }
  new Chart(document.getElementById('returnsHist'), {
    type: 'bar',
    data: {
      labels: histLabels,
      datasets: [
        { label: compStrat.name, data: compStrat.returns_histogram.counts,
          backgroundColor: compStrat.color, borderRadius: 4 },
        { label: 'Buy & Hold', data: bhStrat.returns_histogram.counts,
          backgroundColor: 'rgba(148, 163, 184, 0.6)', borderRadius: 4 }
      ]
    },
    options: {
      scales: {
        x: { title: { display: true, text: 'Weekly return bucket' },
             ticks: { maxRotation: 60, minRotation: 45, font: { size: 10 } } },
        y: { title: { display: true, text: 'count of weeks' } }
      },
      plugins: { legend: { position: 'bottom' } }
    }
  });

  // ─── Decision trace: engines + composite + price (dual axis) ───
  const dt = DATA.decision_trace;
  new Chart(document.getElementById('decisionTrace'), {
    type: 'line',
    data: {
      labels: dt.dates,
      datasets: [
        { label: 'price', data: dt.price, borderColor: '#94a3b8', borderWidth: 1.5,
          backgroundColor: 'transparent', tension: 0.1, pointRadius: 0, yAxisID: 'yPrice' },
        { label: 'composite stance', data: dt.composite_stance, borderColor: '#38bdf8',
          backgroundColor: 'transparent', stepped: true, pointRadius: 0, borderWidth: 2, yAxisID: 'yVote' },
        { label: 'tech momentum', data: dt.technical_momentum, borderColor: '#22c55e',
          backgroundColor: 'transparent', stepped: true, pointRadius: 0, borderWidth: 1.5, yAxisID: 'yVote' },
        { label: 'risk quality', data: dt.risk_quality, borderColor: '#a78bfa',
          backgroundColor: 'transparent', stepped: true, pointRadius: 0, borderWidth: 1.5, yAxisID: 'yVote' },
        { label: 'news sentiment', data: dt.news_sentiment, borderColor: '#fbbf24',
          backgroundColor: 'transparent', stepped: true, pointRadius: 0, borderWidth: 1.5, yAxisID: 'yVote' },
      ]
    },
    options: {
      responsive: true,
      interaction: { intersect: false, mode: 'index' },
      scales: {
        x: { ticks: { maxTicksLimit: 10 } },
        yVote: { type: 'linear', position: 'left', min: -1.2, max: 1.2,
          title: { display: true, text: 'engine vote' },
          ticks: { stepSize: 1, callback: v => v === 1 ? 'BUY' : v === 0 ? 'HOLD' : v === -1 ? 'SELL' : '' } },
        yPrice: { type: 'linear', position: 'right', title: { display: true, text: 'price' },
          grid: { drawOnChartArea: false } }
      },
      plugins: { legend: { position: 'bottom', maxHeight: 60,
        labels: { padding: 10, font: { size: 11 }, boxWidth: 14 } } }
    }
  });

  // ─── Feature evolution: 4 small line charts with sparse-data guard ───
  // When a series is >70% null (e.g. news_sentiment for tickers whose
  // historical headlines aren't on yfinance), drawing it as a sparse
  // line on a phone looks broken. We swap the canvas for a clearly-
  // labeled "limited history" card so users understand the data gap.

  function nullFraction(arr) {
    if (!arr || !arr.length) return 1;
    let n = 0;
    for (const v of arr) if (v === null || v === undefined) n++;
    return n / arr.length;
  }

  function renderMini(canvasId, label, data, color, emptyTitle, emptyBody) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    if (nullFraction(data) >= 0.70) {
      const nonNull = data.filter(v => v !== null && v !== undefined).length;
      const card = document.createElement('div');
      card.className = 'mini-empty';
      card.innerHTML =
        '<div class="mini-empty__icon" aria-hidden="true">!</div>' +
        '<div class="mini-empty__title">' + emptyTitle + '</div>' +
        '<div class="mini-empty__body">' + emptyBody + '</div>' +
        '<div class="mini-empty__meta">' + nonNull + ' of ' + data.length + ' weeks have data</div>';
      canvas.replaceWith(card);
      return;
    }
    new Chart(canvas, {
      type: 'line',
      data: {
        labels: DATA.feature_evolution.dates,
        datasets: [{
          label: label, data: data, borderColor: color,
          backgroundColor: color + '22', fill: true,
          tension: 0.2, pointRadius: 0, borderWidth: 2, spanGaps: false,
        }]
      },
      options: {
        scales: { x: { ticks: { maxTicksLimit: 5, font: { size: 10 } } },
                  y: { ticks: { font: { size: 10 } } } },
        plugins: { legend: { display: false } }
      }
    });
  }
  const fe = DATA.feature_evolution;
  renderMini('featRet20', '20d return',
    fe.return_20d.map(v => v === null ? null : v * 100), '#22c55e',
    '20d return — insufficient history',
    'Need at least 20 trading days of bars before the metric is defined.');
  renderMini('featVol20', '20d volatility',
    fe.volatility_20d.map(v => v === null ? null : v * 100), '#fb923c',
    '20d volatility — insufficient history',
    'Need at least 20 trading days of bars before annualized vol is defined.');
  renderMini('featSent', 'news sentiment',
    fe.news_sentiment_7d, '#fbbf24',
    'News sentiment — limited history',
    'yfinance only exposes the last ~7-30 days of headlines, so past-week sentiment cannot be reconstructed. Current-week sentiment is shown in the engine panel above.');
  renderMini('featComposite', 'composite',
    fe.composite_score, '#38bdf8',
    'Composite — insufficient history',
    'Composite needs at least one engine with usable data per week.');
</script>
</body></html>
"""


def _fmt_pct_html(v, digits=2):
    return f"{v * 100:+.{digits}f}%" if v is not None else "n/a"


def _fmt_num_html(v, digits=2):
    return f"{v:.{digits}f}" if v is not None else "n/a"


def _sentiment_summary(items: list[NewsItem]) -> dict:
    if not items:
        return {"total": 0, "positive": 0, "neutral": 0, "negative": 0, "mean_compound": 0.0}
    pos = sum(1 for i in items if i.sentiment_label == "positive")
    neg = sum(1 for i in items if i.sentiment_label == "negative")
    return {
        "total": len(items),
        "positive": pos,
        "neutral": len(items) - pos - neg,
        "negative": neg,
        "mean_compound": round(sum(i.sentiment_compound for i in items) / len(items), 3),
    }


def _heatmap_color(v: float) -> str:
    """Map a monthly return to an rgba background — red→clear→green by magnitude."""
    if v > 0:
        alpha = min(1.0, abs(v) * 8)  # 12.5% saturates fully
        return f"rgba(34, 197, 94, {alpha:.2f})"
    if v < 0:
        alpha = min(1.0, abs(v) * 8)
        return f"rgba(239, 68, 68, {alpha:.2f})"
    return "rgba(148, 163, 184, 0.10)"


def _build_monthly_heatmap_html(monthly_returns: dict) -> str:
    if not monthly_returns:
        return "<div style='color: var(--muted); font-size: 13px;'>(no monthly data)</div>"
    by_year: dict = {}
    for k, v in monthly_returns.items():
        try:
            year, month = k.split("-")
        except ValueError:
            continue
        by_year.setdefault(int(year), {})[int(month)] = v
    years = sorted(by_year.keys())
    months_short = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    out = ['<table class="heatmap"><thead><tr><th></th>']
    out.extend(f"<th>{m}</th>" for m in months_short)
    out.append("<th class='num'>YTD</th></tr></thead><tbody>")
    for y in years:
        out.append(f"<tr><th class='year-label'>{y}</th>")
        ytd = 1.0
        any_data = False
        for m_num in range(1, 13):
            v = by_year[y].get(m_num)
            if v is None:
                out.append("<td class='empty'>·</td>")
            else:
                any_data = True
                ytd *= (1 + v)
                color = _heatmap_color(v)
                out.append(f"<td style='background:{color}'>{v * 100:+.1f}%</td>")
        ytd_pct = (ytd - 1) * 100 if any_data else None
        if ytd_pct is None:
            out.append("<td class='empty'>·</td></tr>")
        else:
            color = _heatmap_color(ytd_pct / 100)
            out.append(f"<td style='background:{color}; font-weight: 700'>{ytd_pct:+.1f}%</td></tr>")
    out.append("</tbody></table>")
    return "".join(out)


def _build_strategy_table_rows(strategy_results: list[dict]) -> str:
    sortable = [r for r in strategy_results if r["key"] != "buy_hold"]
    sortable.sort(key=lambda r: r["metrics"].get("sharpe_ratio") or -999, reverse=True)
    bh = next((r for r in strategy_results if r["key"] == "buy_hold"), None)
    best_key = sortable[0]["key"] if sortable else None
    rows = []
    for r in sortable + ([bh] if bh else []):
        m = r["metrics"]
        cls = "bh" if r["key"] == "buy_hold" else ("best" if r["key"] == best_key else "")
        swatch = f"<span class='swatch' style='background:{r['color']}'></span>"
        name = f"<div class='strat-name'>{swatch}{h(r['name'])}</div>"
        rows.append(
            f"<tr class='{cls}'>"
            f"<td>{name}</td>"
            f"<td><span class='category-tag'>{h(r['category'])}</span></td>"
            f"<td class='num'>{_fmt_pct_html(m.get('total_return'), 1)}</td>"
            f"<td class='num'>{_fmt_pct_html(m.get('annualized_return'), 1)}</td>"
            f"<td class='num'>{_fmt_pct_html(m.get('max_drawdown'), 1)}</td>"
            f"<td class='num'>{_fmt_num_html(m.get('sharpe_ratio'))}</td>"
            f"<td class='num'>{_fmt_num_html(m.get('calmar_ratio'))}</td>"
            f"<td class='num'>{_fmt_pct_html(m.get('volatility'), 0)}</td>"
            f"<td class='num'>{_fmt_pct_html(m.get('win_rate'), 0)}</td>"
            f"<td class='num'>{_fmt_pct_html(m.get('long_share'), 0)}</td>"
            f"<td class='num'>{m.get('trades', 0)}</td>"
            f"</tr>"
        )
    return "\n".join(rows)


def _build_sweep_table_rows(sweep_results: list[dict]) -> str:
    rows = []
    for r in sweep_results:
        m = r["metrics"]
        swatch = f"<span class='swatch' style='background:{r['color']}'></span>"
        name = f"<div class='strat-name'>{swatch}{h(r['name'])}</div>"
        rows.append(
            f"<tr>"
            f"<td>{name}</td>"
            f"<td class='num'>{_fmt_pct_html(m.get('total_return'), 1)}</td>"
            f"<td class='num'>{_fmt_pct_html(m.get('annualized_return'), 1)}</td>"
            f"<td class='num'>{_fmt_pct_html(m.get('max_drawdown'), 1)}</td>"
            f"<td class='num'>{_fmt_num_html(m.get('sharpe_ratio'))}</td>"
            f"<td class='num'>{_fmt_num_html(m.get('calmar_ratio'))}</td>"
            f"<td class='num'>{_fmt_pct_html(m.get('long_share'), 0)}</td>"
            f"<td class='num'>{m.get('trades', 0)}</td>"
            f"</tr>"
        )
    return "\n".join(rows)


def build_html_report(
    ticker: str,
    bars: Bars,
    features: dict,
    engine_outputs: dict,
    composite: dict,
    news_items: list[NewsItem],
    news_7d: list[NewsItem],
    strategy_results: list[dict],
    sweep_results: list[dict],
    feature_evolution: dict,
    decision_trace: dict,
    backtest_start: date,
) -> str:
    # Composite bar geometry: map [-1, 1] → [0, 100]% with bar from midpoint.
    cs = composite["composite_score"]
    if cs >= 0:
        comp_left = 50.0
        comp_width = min(cs, 1.0) * 50.0
        comp_color = "linear-gradient(90deg, #22c55e, #16a34a)"
    else:
        comp_width = min(-cs, 1.0) * 50.0
        comp_left = 50.0 - comp_width
        comp_color = "linear-gradient(90deg, #dc2626, #ef4444)"

    feature_rows = []
    feat_labels = {
        "return_5d": "5-day return",
        "return_20d": "20-day return",
        "return_60d": "60-day return",
        "volatility_20d": "20-day volatility (ann)",
        "drawdown_20d": "20-day max drawdown",
        "relative_volume_20d": "20-day relative volume",
        "news_sentiment_7d": "7-day news sentiment",
        "news_count_7d": "7-day news count",
    }
    feat_kinds = {
        "return_5d": "pct", "return_20d": "pct", "return_60d": "pct",
        "volatility_20d": "pct", "drawdown_20d": "pct",
        "relative_volume_20d": "ratio", "news_sentiment_7d": "score",
        "news_count_7d": "int",
    }
    for key, label in feat_labels.items():
        val, qual = features.get(key, (None, "missing"))
        kind = feat_kinds[key]
        if val is None:
            text_v = "n/a"
        elif kind == "pct":
            text_v = _fmt_pct_html(val)
        elif kind == "int":
            text_v = str(int(val))
        else:
            text_v = _fmt_num_html(val, 3)
        qpill = "pos" if qual == "ok" else "neu"
        feature_rows.append(
            f"<tr><td>{h(label)}</td><td class='num'>{text_v}</td>"
            f"<td><span class='pill {qpill}'>{h(qual)}</span></td></tr>"
        )

    news_html_parts = []
    if not news_items:
        news_html_parts.append("<div class='news-item'>(no news returned by yfinance)</div>")
    for n in news_items[:12]:
        pill = "pos" if n.sentiment_label == "positive" else "neg" if n.sentiment_label == "negative" else "neu"
        link_html = (
            f"<a href='{h(n.link)}' target='_blank' rel='noopener'>{h(n.title)}</a>"
            if n.link else h(n.title)
        )
        news_html_parts.append(
            f"<div class='news-item'>"
            f"<div class='title'>{link_html}</div>"
            f"<div class='src'><span class='pill {pill}'>{n.sentiment_label} {n.sentiment_compound:+.2f}</span> "
            f"· {h(n.publisher)} · {h(n.published or 'undated')}</div>"
            f"</div>"
        )

    drivers_html = "".join(f"<div class='driver'>{h(d)}</div>" for d in composite["drivers"][:6])
    if not drivers_html:
        drivers_html = "<div style='color: var(--muted); font-size: 13px;'>(none)</div>"
    caveats_html = "".join(f"<div class='caveat'>{h(c)}</div>" for c in composite["caveats"][:6])
    if not caveats_html:
        caveats_html = "<div style='color: var(--muted); font-size: 13px;'>(none)</div>"

    # Price curve restricted to backtest window for the chart.
    price_curve = [
        {"date": d.isoformat(), "close": c}
        for d, c in zip(bars.dates, bars.closes, strict=False)
        if d >= backtest_start
    ]

    # Pick the main strategy (composite_010) for the monthly heatmap.
    main = next((r for r in strategy_results if r["key"] == "composite_010"), strategy_results[0] if strategy_results else None)
    monthly_heatmap_html = _build_monthly_heatmap_html(main.get("monthly_returns", {})) if main else ""

    # Trim strategy payload for the JSON blob (drop period_returns to save size)
    strategies_payload = []
    for r in strategy_results:
        strategies_payload.append({
            "key": r["key"],
            "name": r["name"],
            "category": r["category"],
            "color": r["color"],
            "metrics": r["metrics"],
            "equity_curve": r["equity_curve"],
            "drawdown_curve": r["drawdown_curve"],
            "rolling_sharpe": r["rolling_sharpe"],
            "returns_histogram": r["returns_histogram"],
        })

    data_payload = {
        "engines": {
            k: {"score": v.get("score", 0.0), "confidence": v.get("confidence", 0.0),
                "stance": v.get("stance"), "risk_level": v.get("risk_level")}
            for k, v in engine_outputs.items()
        },
        "sentiment_summary": _sentiment_summary(news_7d),
        "price_curve": price_curve,
        "strategies": strategies_payload,
        "feature_evolution": feature_evolution,
        "decision_trace": decision_trace,
    }

    html = _HTML_TEMPLATE
    replacements = {
        "[[CHARTJS_SCRIPT]]": _CHARTJS_SCRIPT_TAG,
        "[[TICKER]]": h(ticker),
        "[[AS_OF]]": h(str(bars.latest_date)),
        "[[LAST_CLOSE]]": _fmt_num_html(bars.latest_close, 2),
        "[[NBARS]]": str(len(bars.dates)),
        "[[GENERATED]]": h(datetime.now(UTC).isoformat(timespec="seconds")),
        "[[STANCE]]": h(composite["stance"].upper()),
        "[[COMPOSITE]]": _fmt_num_html(composite["composite_score"]),
        "[[WEIGHT]]": _fmt_pct_html(composite["target_weight"]),
        "[[AVG_CONF]]": _fmt_num_html(composite["avg_confidence"]),
        "[[N_STRATS]]": str(len(strategy_results)),
        "[[COMPOSITE_COLOR]]": comp_color,
        "[[COMPOSITE_LEFT]]": f"{round(comp_left, 2)}",
        "[[COMPOSITE_WIDTH]]": f"{round(comp_width, 2)}",
        "[[DRIVERS_HTML]]": drivers_html,
        "[[CAVEATS_HTML]]": caveats_html,
        "[[FEATURES_ROWS]]": "\n".join(feature_rows),
        "[[NEWS_HTML]]": "".join(news_html_parts),
        "[[STRATEGY_TABLE_ROWS]]": _build_strategy_table_rows(strategy_results),
        "[[SWEEP_TABLE_ROWS]]": _build_sweep_table_rows(sweep_results),
        "[[MONTHLY_HEATMAP_HTML]]": monthly_heatmap_html,
        "[[DATA_JSON]]": json.dumps(data_payload, default=str),
    }
    for token, value in replacements.items():
        html = html.replace(token, value)
    return html



# ── Top-level entry point ────────────────────────────────────────────────────


@dataclass
class AnalysisResult:
    """Bundle returned by run_full_analysis.

    `html` is a complete, self-contained HTML document with embedded chart
    data. The remaining fields are the raw analysis structures so callers
    (CLI, API, future React UI) can reuse them without re-running the
    pipeline.
    """
    ticker: str
    html: str
    bars: Bars
    features: dict
    engine_outputs: dict
    composite: dict
    news_items: list
    news_7d: list
    strategy_results: list[dict]
    sweep_results: list[dict]
    feature_evolution: dict
    decision_trace: dict
    backtest_start: date


def run_full_analysis(
    ticker: str,
    *,
    history_days: int = 400,
    backtest_days: int = 365,
) -> AnalysisResult:
    """End-to-end ticker analysis.

    Raises ValueError on bad input (e.g. empty ticker), RuntimeError on
    data-fetch failure (yfinance returned nothing for that symbol).
    Takes ~5-10 seconds for a 1-year backtest window.
    """
    sym = ticker.upper().strip()
    if not sym:
        raise ValueError("ticker must be non-empty")

    total_history = max(history_days, backtest_days + 120)
    bars = fetch_history(sym, total_history)
    if not bars.dates:
        raise RuntimeError(f"yfinance returned no data for {sym}")

    news_items, news_ok = fetch_news(sym)
    news_7d = news_within(news_items, days=7)
    news_scores_7d = [n.sentiment_compound for n in news_7d]
    features = compute_features(
        bars.closes, bars.volumes, news_scores_7d, news_source_exists=news_ok
    )
    engine_outputs = {k: fn(features) for k, fn in ENGINE_FUNCTIONS.items()}
    composite = composite_recommendation(engine_outputs)

    backtest_start = bars.dates[-1] - timedelta(days=backtest_days)
    backtest_start = max(backtest_start, bars.dates[60])
    rebalances = _generate_weekly_rebalances(backtest_start, bars.dates[-1])
    states = precompute_rebalance_states(bars, news_items, rebalances)

    main_strategies = build_main_strategies()
    threshold_sweep = build_threshold_sweep()
    strategy_results = [run_strategy(states, s) for s in main_strategies]
    sweep_results = [run_strategy(states, s) for s in threshold_sweep]

    feature_evolution = collect_feature_evolution(states)
    decision_trace = collect_decision_trace(states)

    html = build_html_report(
        ticker=sym, bars=bars, features=features,
        engine_outputs=engine_outputs, composite=composite,
        news_items=news_items, news_7d=news_7d,
        strategy_results=strategy_results, sweep_results=sweep_results,
        feature_evolution=feature_evolution, decision_trace=decision_trace,
        backtest_start=backtest_start,
    )

    return AnalysisResult(
        ticker=sym, html=html, bars=bars, features=features,
        engine_outputs=engine_outputs, composite=composite,
        news_items=news_items, news_7d=news_7d,
        strategy_results=strategy_results, sweep_results=sweep_results,
        feature_evolution=feature_evolution, decision_trace=decision_trace,
        backtest_start=backtest_start,
    )
