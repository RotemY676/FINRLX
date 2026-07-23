"""PROGRAM LEAP S2/S4 — Autopilot Research Engine.

The simple user's contract: a ticker in, a 360-degree research dossier out,
zero configuration. This module orchestrates the staged pipeline
(ingest -> enrich -> features -> tournament -> dossier) on top of the
proven primitives in `single_ticker_analysis`, and adds the automatic
model tournament (Decision Register D34-D37, D39-D40).

Truthfulness invariants (D30, D37):
- A dossier is research analysis, never investment advice; every dossier
  carries explicit disclaimers.
- The tournament winner is always explained: full scoreboard, train/val
  divergence, and the multiple-testing (deflation) penalty are persisted
  and rendered — never a bare "the AI picked X".
- Reinforcement-learning candidates run only via the isolated research
  container. When that path is unavailable in the serving environment,
  the RL leg degrades to an honest `queued_for_research_run` status
  (D35 fallback) instead of pretending.
- Nothing here reads or writes the governed recommendation/publication
  pipeline. Dossiers are a separate research surface (like /analyze).

Determinism: seeded models, fixed candidate order, and a config-version
string in the cache key so any scoring change invalidates old dossiers.
"""
from __future__ import annotations

import logging
import math
import re
import time
from dataclasses import dataclass
from threading import Lock
from typing import Callable

from app.services.freshness_state import freshness_state_from_latest
from app.services.single_ticker_analysis import (
    Bars,
    RebalanceState,
    StrategyDef,
    _generate_weekly_rebalances,
    build_main_strategies,
    composite_recommendation,
    compute_features,
    fetch_history,
    fetch_news,
    news_within,
    precompute_rebalance_states,
    rsi,
    run_strategy,
    sma,
)
from app.services.uncertainty import uncertainty_block

logger = logging.getLogger(__name__)

CONFIG_VERSION = "a1-leap-s4-v1"
TICKER_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9.\-]{0,9}$")

# D39 defaults (zero-config: constants, not user settings)
HISTORY_DAYS_DEFAULT = 750
N_SPLITS = 3
DIVERGENCE_LAMBDA = 0.5
RANDOM_SEED = 42
MIN_STATES_FOR_TOURNAMENT = 30

DISCLAIMERS = [
    "Research analysis, not investment advice.",
    "Past performance does not guarantee future results.",
    "Model selection is automatic and validation-based; all candidates and penalties are shown.",
]

_COMPLEXITY = {"benchmark": 0, "heuristic": 0, "ml": 1, "rl": 2}


# ── Walk-forward splitting (D36) ─────────────────────────────────────────────

def walk_forward_splits(n_states: int, n_splits: int = N_SPLITS) -> list[tuple[int, int]]:
    """Expanding train / contiguous forward validation splits over the
    rebalance-state index space. Returns [(train_end, val_end), ...] with
    train = states[:train_end], validation = states[train_end:val_end].
    Validation windows are non-overlapping and strictly after their train
    window — leakage is impossible by construction.
    """
    if n_states < MIN_STATES_FOR_TOURNAMENT:
        return []
    first_train_end = max(10, n_states // 2)
    remaining = n_states - first_train_end
    val_len = max(4, remaining // n_splits)
    splits: list[tuple[int, int]] = []
    train_end = first_train_end
    while len(splits) < n_splits and train_end + val_len <= n_states:
        splits.append((train_end, min(train_end + val_len, n_states)))
        train_end += val_len
    return splits


def _sharpe_of(states: list[RebalanceState], decide: Callable[[RebalanceState], float]) -> float:
    if len(states) < 3:
        return 0.0
    sdef = StrategyDef("tmp", "tmp", "tmp", "#000", "", decide)
    metrics = run_strategy(states, sdef).get("metrics", {})
    # BUGFIX 2026-07-23: run_strategy emits the Sharpe under "sharpe_ratio", not
    # "sharpe". This read `metrics.get("sharpe")` -> always None -> every
    # candidate scored val_sharpe 0.0 across every split, so the tournament's
    # "winner" was never validated — it was whichever candidate the tie-break
    # happened to surface (all rows collapsed to -deflation_penalty). The
    # walk-forward model selection, the product's stated moat, had been inert.
    # Verified live: 8/8 candidates at 0.0 on 515 fresh bars before this fix.
    s = metrics.get("sharpe_ratio")
    if s is None or (isinstance(s, float) and (math.isnan(s) or math.isinf(s))):
        return 0.0
    return float(s)


# ── Candidates ───────────────────────────────────────────────────────────────

@dataclass
class Candidate:
    key: str
    name: str
    kind: str  # heuristic | benchmark | ml | rl
    description: str
    # For heuristic/benchmark: a state-decide function.
    decide: Callable[[RebalanceState], float] | None = None
    # For ML: fit(train)->decide-for-any-state closure per split.
    fit: Callable[[list[RebalanceState]], Callable[[RebalanceState], float]] | None = None


def _fval(features: dict, key: str) -> float:
    """Unwrap the project's (value, status) feature tuples to a float."""
    raw = features.get(key)
    if isinstance(raw, tuple):
        raw = raw[0]
    return float(raw) if raw is not None else 0.0


def _flatten_features(features: dict) -> dict:
    out = {}
    for k, v in features.items():
        if isinstance(v, tuple):
            out[k] = {"value": v[0], "status": v[1]}
        else:
            out[k] = {"value": v, "status": "ok"}
    return out


def _state_feature_vector(st: RebalanceState) -> list[float]:
    """Numeric features available AT the state's own date (<= t only)."""
    f = st.features
    closes = st.window.closes
    vec = [
        _fval(f, "return_5d"),
        _fval(f, "return_20d"),
        _fval(f, "return_60d"),
        _fval(f, "volatility_20d"),
        _fval(f, "drawdown_20d"),
        _fval(f, "news_sentiment_7d"),
        float(st.engines.get("technical_momentum", {}).get("score") or 0.0),
        float(st.engines.get("risk_quality", {}).get("score") or 0.0),
        float(st.engines.get("news_sentiment", {}).get("score") or 0.0),
        float((rsi(closes) or 50.0) / 100.0),
    ]
    s20, s50 = sma(closes, 20), sma(closes, 50)
    vec.append(1.0 if (s20 is not None and s50 is not None and s20 > s50) else 0.0)
    return vec


def _make_ml_fit() -> Callable[[list[RebalanceState]], Callable[[RebalanceState], float]]:
    """Gradient-boosted next-period return forecaster (D35b, D21').

    Trains ONLY on the provided train slice: X_i = features(state_i),
    y_i = return from state_i to state_{i+1} — both fully inside train,
    so no validation information ever reaches the fit.
    Falls back to a tiny in-house ridge if scikit-learn is unavailable.
    """
    def fit(train: list[RebalanceState]) -> Callable[[RebalanceState], float]:
        X, y = [], []
        for a, b in zip(train, train[1:], strict=False):
            X.append(_state_feature_vector(a))
            y.append((b.price - a.price) / a.price if a.price else 0.0)
        if len(X) < 8:
            return lambda st: 0.0
        try:
            from sklearn.ensemble import HistGradientBoostingRegressor
            model = HistGradientBoostingRegressor(
                max_iter=60, max_depth=3, learning_rate=0.08,
                random_state=RANDOM_SEED,
            )
            model.fit(X, y)
            predict = lambda v: float(model.predict([v])[0])  # noqa: E731
        except Exception:  # pragma: no cover — sklearn missing/broken (D21' fallback)
            predict = _ridge_predictor(X, y)
        return lambda st: 1.0 if predict(_state_feature_vector(st)) > 0.0 else 0.0

    return fit


def _ridge_predictor(X: list[list[float]], y: list[float]) -> Callable[[list[float]], float]:
    """Minimal ridge regression (normal equations, lam*I), dependency-free."""
    n_feat = len(X[0])
    lam = 1.0
    XtX = [[sum(r[i] * r[j] for r in X) + (lam if i == j else 0.0)
            for j in range(n_feat)] for i in range(n_feat)]
    Xty = [sum(r[i] * t for r, t in zip(X, y, strict=False)) for i in range(n_feat)]
    # Gaussian elimination
    A = [row[:] + [Xty[i]] for i, row in enumerate(XtX)]
    for col in range(n_feat):
        piv = max(range(col, n_feat), key=lambda r: abs(A[r][col]))
        A[col], A[piv] = A[piv], A[col]
        if abs(A[col][col]) < 1e-12:
            continue
        for r in range(n_feat):
            if r != col and abs(A[r][col]) > 1e-12:
                f = A[r][col] / A[col][col]
                A[r] = [a - f * b for a, b in zip(A[r], A[col], strict=False)]
    w = [A[i][n_feat] / A[i][i] if abs(A[i][i]) > 1e-12 else 0.0 for i in range(n_feat)]
    return lambda v: sum(wi * vi for wi, vi in zip(w, v, strict=False))


def build_candidates() -> list[Candidate]:
    cands: list[Candidate] = []
    for s in build_main_strategies():
        kind = "benchmark" if s.key == "buy_hold" else "heuristic"
        cands.append(Candidate(s.key, s.name, kind, s.description, decide=s.decide))
    cands.append(Candidate(
        "ml_gbr", "ML return forecaster (gradient boosting)", "ml",
        "HistGradientBoosting on price/vol/drawdown/news/engine features; "
        "long when the predicted next-period return is positive. "
        "Refit per walk-forward split on train data only.",
        fit=_make_ml_fit(),
    ))
    return cands


# ── Tournament (D36, D37) ────────────────────────────────────────────────────

def run_tournament(states: list[RebalanceState], ticker: str | None = None) -> dict:
    splits = walk_forward_splits(len(states))
    candidates = build_candidates()
    n_eligible = len(candidates)

    if not splits:
        return {
            "status": "insufficient_history",
            "note": (
                f"Fewer than {MIN_STATES_FOR_TOURNAMENT} weekly observations — "
                "the tournament needs more history to validate candidates honestly."
            ),
            "config_version": CONFIG_VERSION,
            "candidates": [], "winner": None, "rl": _rl_leg_status(),
        }

    n_val_periods = sum(v - t for t, v in splits)
    deflation_penalty = round(math.sqrt(math.log(max(n_eligible, 2)) / max(n_val_periods, 2)), 4)

    rows = []
    for cand in candidates:
        train_sharpes, val_sharpes = [], []
        for train_end, val_end in splits:
            train = states[:train_end]
            val = states[train_end:val_end]
            decide = cand.fit(train) if cand.fit is not None else cand.decide
            train_sharpes.append(_sharpe_of(train, decide))
            val_sharpes.append(_sharpe_of(val, decide))
        train_s = sum(train_sharpes) / len(train_sharpes)
        val_s = sum(val_sharpes) / len(val_sharpes)
        divergence = abs(train_s - val_s)
        score = val_s - DIVERGENCE_LAMBDA * divergence - deflation_penalty
        rows.append({
            "key": cand.key, "name": cand.name, "kind": cand.kind,
            "description": cand.description,
            "train_sharpe": round(train_s, 3),
            "val_sharpe": round(val_s, 3),
            "divergence": round(divergence, 3),
            "penalty": deflation_penalty,
            "score": round(score, 3),
            "eligible": True,
            "per_split_val_sharpe": [round(v, 3) for v in val_sharpes],
        })

    # Ties break toward the simpler model (D36): heuristic > ml > rl.
    # LEAP A3 (D45): merge FinRL ensemble agents from the research artifact
    # (if published for this ticker) under the SAME protocol + re-deflated
    # penalties; absent/rejected artifacts leave rows untouched.
    rl_status = _rl_leg_status()
    if ticker:
        try:
            from app.services.finrl_ensemble import merge_rl_candidates

            rows, rl_status = merge_rl_candidates(
                ticker, rows, splits, n_val_periods, DIVERGENCE_LAMBDA
            )
            deflation_penalty = rows[0]["penalty"] if rows else deflation_penalty
            n_eligible = len(rows)
        except Exception as _exc:  # noqa: BLE001 — artifact path never sinks the tournament
            logger.warning("ensemble merge failed for %s: %s", ticker, _exc)

    ranked = sorted(rows, key=lambda r: (-r["score"], _COMPLEXITY.get(r["kind"], 9), r["key"]))
    winner = ranked[0]
    rationale = (
        f"Selected '{winner['name']}' — highest validation score "
        f"({winner['score']}) across {len(splits)} walk-forward splits after an "
        f"overfitting-divergence penalty (|train−val| × {DIVERGENCE_LAMBDA}) and a "
        f"multiple-testing deflation of {deflation_penalty} for comparing "
        f"{n_eligible} candidates. Ties favor simpler models."
    )
    return {
        "status": "complete",
        "config_version": CONFIG_VERSION,
        "n_splits": len(splits),
        "n_val_periods": n_val_periods,
        "deflation_penalty": deflation_penalty,
        "candidates": ranked,
        "winner": {**winner, "rationale": rationale},
        "rl": rl_status,
        "seed": RANDOM_SEED,
    }


def _rl_leg_status() -> dict:
    """D35 fallback, stated honestly. Torch/SB3 live only in the isolated
    research container; the serving backend deliberately excludes them."""
    try:  # pragma: no cover — presence check only
        import stable_baselines3  # noqa: F401
        available = True
    except Exception:
        available = False
    if available:
        return {"status": "available", "note": "RL candidates run via the research container path."}
    return {
        "status": "queued_for_research_run",
        "candidates": ["PPO (small config)", "A2C (small config)"],
        "note": (
            "Reinforcement-learning candidates train only in the isolated "
            "research environment (research/finrlx_cpu) and were not run in "
            "this serving environment. When a research run is imported, its "
            "candidates join this scoreboard with the same scoring."
        ),
        "eligible": False,
    }


# ── Regime label (D5-lite, research overlay language) ────────────────────────

def regime_label(bars: Bars) -> dict:
    closes = bars.closes
    s20, s50 = sma(closes, 20), sma(closes, 50)
    dd20 = None
    if len(closes) >= 21:
        window = closes[-21:]
        peak = max(window)
        dd20 = (window[-1] - peak) / peak if peak else 0.0
    if dd20 is not None and dd20 <= -0.12:
        label, detail = "risk-off", "20-day drawdown beyond −12%"
    elif s20 is not None and s50 is not None and s20 > s50 and closes[-1] > s50:
        label, detail = "uptrend", "price above SMA50 and SMA20 > SMA50"
    elif s20 is not None and s50 is not None and s20 < s50:
        label, detail = "downtrend", "SMA20 below SMA50"
    else:
        label, detail = "neutral", "no dominant trend signal"
    return {
        "label": label,
        "detail": detail,
        "kind": "research overlay — rule-based label, not a prediction",
        "sma20": round(s20, 4) if s20 is not None else None,
        "sma50": round(s50, 4) if s50 is not None else None,
        "drawdown_20d": round(dd20, 4) if dd20 is not None else None,
    }


# ── Dossier assembly (D31 data, E.4 schema) ──────────────────────────────────

_cache_lock = Lock()
_dossier_cache: dict[tuple[str, str, str], dict] = {}
_CACHE_MAX = 64


def validate_ticker(raw: str) -> str:
    sym = (raw or "").upper().strip()
    if not TICKER_PATTERN.match(sym):
        raise ValueError(
            f"Invalid ticker symbol: {raw!r}. Use 1-10 letters/digits/dot/dash."
        )
    return sym


def _timed(stages: list, name: str, fn):
    """Run a section builder with timing + total failure containment."""
    import time as _time

    t0 = _time.time()
    try:
        out = fn()
    except Exception as exc:  # noqa: BLE001 — sections never sink a dossier
        logger.warning("dossier section %s failed: %s", name, exc)
        out = {"available": False, "reason": "section_error", "source": name}
    stages.append({"stage": name, "ms": int((_time.time() - t0) * 1000)})
    return out


def _section_fundamentals(ticker: str, stages: list) -> dict:
    """LEAP A1 (D43): SEC XBRL trends (keyless, always attempted) + the
    existing Finnhub fundamentals snapshot when that provider is configured.
    Context only — never feeds stances (regression-tested)."""

    def _build():
        from app.services.data_providers.sec_xbrl import build_xbrl_trends
        from app.services.fundamentals.router import get_provider

        xbrl = build_xbrl_trends(ticker)
        snapshot: dict = {"available": False, "reason": "provider_not_configured"}
        provider = get_provider()
        if provider is not None and provider.__class__.__name__ != "StubFundamentalsProvider":
            import asyncio

            try:
                resp = asyncio.run(provider.get_fundamentals(ticker))
                snapshot = {"available": True, "source": "finnhub", **(
                    resp.model_dump() if hasattr(resp, "model_dump") else dict(resp)
                )}
            except Exception as exc:  # noqa: BLE001
                snapshot = {"available": False, "reason": str(exc)[:120]}
        return {
            "available": bool(xbrl.get("available") or snapshot.get("available")),
            "xbrl": xbrl,
            "snapshot": snapshot,
            "note": None if (xbrl.get("available") or snapshot.get("available")) else (
                "No fundamentals source reachable (SEC XBRL had no usable facts "
                "and no provider is configured); the analysis does not depend on them."
            ),
        }

    return _timed(stages, "fundamentals", _build)


def _section_filings(ticker: str, stages: list) -> dict:
    def _build():
        from app.services.data_providers.finnhub_extras import (
            filings_tone,
            similarity_index,
        )

        tone = filings_tone(ticker)
        sim = similarity_index(ticker)
        return {
            "available": bool(tone.get("available") or sim.get("available")),
            "tone": tone,
            "similarity": sim,
        }

    return _timed(stages, "filings", _build)


def _section_insider(ticker: str, stages: list) -> dict:
    def _build():
        from app.services.data_providers.finnhub_extras import insider_sentiment

        return insider_sentiment(ticker)

    return _timed(stages, "insider", _build)


def _build_desk_block(sym, bars, news_item_dicts, filings_section,
                      insider_section, rebalances, states, price_series):
    """LEAP A4 (D46-D48): everything the Analyst Desk chart/matrix/arena need."""
    from app.services.desk_payload import (
        event_markers,
        regime_band_series,
        signal_matrix,
        split_windows,
    )

    chart_start = price_series[0]["date"] if price_series else "1900-01-01"
    state_dates = [st.date for st in states]
    splits = walk_forward_splits(len(states))
    from app.services.single_ticker_analysis import compute_features as _cf

    flat = _flatten_features(_cf(bars.closes, bars.volumes, [], news_source_exists=False))
    return {
        "available": True,
        "regime_bands": regime_band_series(bars),
        "event_markers": event_markers(
            sym, news_item_dicts, filings_section, insider_section,
            rebalances, chart_start,
        ),
        "signal_matrix": signal_matrix(bars, flat),
        "split_windows": split_windows(state_dates, splits),
    }


def build_dossier(ticker: str, *, history_days: int = HISTORY_DAYS_DEFAULT) -> dict:
    """The full autopilot pipeline for one ticker. Synchronous v1 with
    per-stage timings persisted in the payload; cache-backed (D34)."""
    sym = validate_ticker(ticker)
    stages: list[dict] = []

    def stage(name: str):
        rec = {"stage": name, "started_at": time.time()}
        stages.append(rec)
        return rec

    def done(rec: dict):
        rec["ms"] = int((time.time() - rec.pop("started_at")) * 1000)

    s = stage("ingest — price history")
    bars = fetch_history(sym, history_days)
    done(s)
    if not bars.dates:
        raise RuntimeError(f"No price data available for {sym}")

    latest = bars.dates[-1]
    cache_key = (sym, latest.isoformat(), CONFIG_VERSION)
    with _cache_lock:
        cached = _dossier_cache.get(cache_key)
    if cached is not None:
        out = dict(cached)
        out["served_from_cache"] = True
        return out

    s = stage("enrich — news and sentiment")
    news_items, news_ok = fetch_news(sym)
    news_7d = news_within(news_items, days=7)
    done(s)

    s = stage("features — technical vocabulary")
    features = compute_features(
        bars.closes, bars.volumes,
        [n.sentiment_compound for n in news_7d],
        news_source_exists=news_ok,
    )
    from app.services.single_ticker_analysis import ENGINE_FUNCTIONS
    engine_outputs = {k: fn(features) for k, fn in ENGINE_FUNCTIONS.items()}
    composite = composite_recommendation(engine_outputs)
    regime = regime_label(bars)
    done(s)

    s = stage("tournament — automatic model selection")
    start = bars.dates[max(0, min(60, len(bars.dates) - 1))]
    rebalances = _generate_weekly_rebalances(start, latest)
    states = precompute_rebalance_states(bars, news_items, rebalances)
    tournament = run_tournament(states, ticker=sym)
    done(s)

    s = stage("dossier — assembly")
    price_series = [
        {"date": d.isoformat(), "close": round(c, 4)}
        for d, c in zip(bars.dates, bars.closes, strict=False)
    ][-260:]
    news_counts: dict[str, int] = {}
    for n in news_items:
        news_counts[n.sentiment_label] = news_counts.get(n.sentiment_label, 0) + 1
    # LEAP A2 (D43/D44): social lane + measured media-vs-social divergence.
    def _build_social():
        from app.services.data_providers.social_sentiment import (
            build_social_lane,
            compute_divergence,
        )

        lane = build_social_lane(sym)
        media_avg = (
            sum(n.sentiment_compound for n in news_7d) / len(news_7d)
            if news_7d else None
        )
        return lane, compute_divergence(media_avg, lane)

    try:
        _social, _divergence = _build_social()
    except Exception as _exc:  # noqa: BLE001 — lane can never sink a dossier
        logger.warning("social lane failed: %s", _exc)
        _social = {"available": False, "reason": "section_error", "source": "social"}
        _divergence = {"status": "not_applicable", "reason": "social lane errored"}
    _news_item_dicts = [
        {"date": n.published.isoformat() if hasattr(n.published, "isoformat") else str(n.published),
         "title": n.title, "sentiment": n.sentiment_label,
         "compound": round(n.sentiment_compound, 3)}
        for n in news_7d[:10]
    ]
    try:
        from app.services.fingpt_lane import attach_llm_scores
        _fingpt_status = attach_llm_scores(sym, _news_item_dicts)
    except Exception as _exc:  # noqa: BLE001
        logger.warning("fingpt lane failed: %s", _exc)
        _fingpt_status = {"status": "lane_error"}
    _filings_holder = _section_filings(ticker, stages)
    _insider_holder = _section_insider(ticker, stages)
    dossier = {
        "ticker": sym,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "config_version": CONFIG_VERSION,
        "freshness": {
            "latest_bar": latest.isoformat(),
            "bars": len(bars.dates),
            "news_source_available": news_ok,
        },
        "summary": {
            "latest_close": bars.latest_close,
            "stance": composite["stance"],
            "composite_score": composite["composite_score"],
            "avg_confidence": composite["avg_confidence"],
            "regime": regime["label"],
            "stance_kind": "research stance from the FINRLX engine ensemble — not advice",
            # Phase 6: uncertainty that moves the threshold rather than
            # annotating the answer. Reported alongside the engine stance, not
            # substituted for it — when the two differ, that difference is the
            # finding and the reader should see it stated.
            "uncertainty": uncertainty_block(
                composite_score=composite["composite_score"],
                avg_confidence=composite["avg_confidence"],
                engine_scores=[
                    e.get("score") for e in engine_outputs.values()
                    if isinstance(e, dict) and isinstance(e.get("score"), int | float)
                ],
                sessions=len(bars.dates),
                is_stale=freshness_state_from_latest(latest).is_stale,
            ),
        },
        "sections": {
            "technical": {
                "available": True,
                "features": _flatten_features(features),
                "regime": regime,
                "engines": engine_outputs,
                "composite": composite,
            },
            "news_sentiment": {
                "available": news_ok,
                "note": None if news_ok else "News source unavailable — section degraded, analysis continued without it.",
                "counts": news_counts,
                "social": _social,
                "divergence": _divergence,
                "fingpt_lane": _fingpt_status,
                "items_7d": _news_item_dicts,
            },
            "fundamentals": _section_fundamentals(ticker, stages),
            "filings": _filings_holder,
            "insider": _insider_holder,
            "model_insight": tournament,
            "desk": _timed(stages, "desk", lambda: _build_desk_block(
                sym, bars, _news_item_dicts,
                _filings_holder, _insider_holder,
                rebalances, states, price_series,
            )),
        },
        "price_series": price_series,
        "stages": stages,
        "disclaimers": DISCLAIMERS,
        "served_from_cache": False,
    }
    done(s)

    with _cache_lock:
        if len(_dossier_cache) >= _CACHE_MAX:
            _dossier_cache.pop(next(iter(_dossier_cache)))
        _dossier_cache[cache_key] = dossier
    return dossier
