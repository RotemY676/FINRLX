"""LEAP A4 — Analyst Desk payload builders (decisions D46–D48).

Pure functions over bars + existing dossier sections; the autopilot pipeline
attaches the result as `sections.desk` and the D42 section endpoints slice it.

  regime_band_series(bars)     per-session regime labels (the SAME rule set
                               as the live regime_label — D47), compressed
                               into contiguous bands; closes DEBT-S5-2
  event_markers(...)           {date, type, label, evidence_ref} from news /
                               filings / insider / rebalances (D46)
  signal_matrix(bars, ...)     per feature: value, percentile vs its own
                               trailing history, 60-session sparkline,
                               plain-language read (D48)
  split_windows(...)           walk-forward train/validation date ranges for
                               the tournament-arena timeline drawing

Honesty: percentiles need >=1y of the feature's own history or they are
omitted with "insufficient history"; band labels reuse the production rule
verbatim (no invented history); markers always carry an evidence_ref.
"""
from __future__ import annotations

from bisect import bisect_left
from datetime import date

from app.services.single_ticker_analysis import (
    Bars,
    _compute_drawdown,
    _compute_return,
    _compute_volatility,
    sma,
)

MIN_PERCENTILE_HISTORY = 252  # ~1 trading year
SPARKLINE_SESSIONS = 60

__all__ = [
    "regime_band_series",
    "event_markers",
    "signal_matrix",
    "split_windows",
]


# ── D47: regime bands ────────────────────────────────────────────────────────


def _regime_at(closes: list[float]) -> str:
    """The production regime rule (autopilot.regime_label) applied to a
    prefix of closes — kept in exact rule parity, verified by test."""
    s20, s50 = sma(closes, 20), sma(closes, 50)
    dd20 = None
    if len(closes) >= 21:
        window = closes[-21:]
        peak = max(window)
        dd20 = (window[-1] - peak) / peak if peak else 0.0
    if dd20 is not None and dd20 <= -0.12:
        return "risk-off"
    if s20 is not None and s50 is not None and s20 > s50 and closes[-1] > s50:
        return "uptrend"
    if s20 is not None and s50 is not None and s20 < s50:
        return "downtrend"
    return "neutral"


def regime_band_series(bars: Bars, max_sessions: int = 260) -> list[dict]:
    """Contiguous {start, end, label} bands over the charted window."""
    n = len(bars.closes)
    if n < 51:
        return []
    start_idx = max(50, n - max_sessions)
    bands: list[dict] = []
    for i in range(start_idx, n):
        label = _regime_at(bars.closes[: i + 1])
        day = bars.dates[i].isoformat()
        if bands and bands[-1]["label"] == label:
            bands[-1]["end"] = day
        else:
            bands.append({"start": day, "end": day, "label": label})
    return bands


# ── D46: event markers ───────────────────────────────────────────────────────


def event_markers(
    ticker: str,
    news_items: list[dict],
    filings_section: dict,
    insider_section: dict,
    rebalance_dates: list[date],
    chart_start: str,
) -> list[dict]:
    markers: list[dict] = []
    for item in news_items:
        if item.get("date"):
            markers.append({
                "date": str(item["date"])[:10],
                "type": "news",
                "label": (item.get("title") or "")[:80],
                "evidence_ref": f"section:news_sentiment#item:{item.get('date')}",
            })
    tone = (filings_section or {}).get("tone") or {}
    if tone.get("available") and tone.get("filed_date"):
        markers.append({
            "date": str(tone["filed_date"])[:10],
            "type": "filing",
            "label": f"{tone.get('form')} filed",
            "evidence_ref": "section:filings#tone",
        })
    ins = insider_section or {}
    if ins.get("available"):
        for row in (ins.get("series_12m") or [])[-3:]:
            if row.get("net_change") and row.get("year") and row.get("month"):
                markers.append({
                    "date": f"{row['year']}-{row['month']:02d}-15",
                    "type": "insider",
                    "label": f"insider net change {row['net_change']:+}",
                    "evidence_ref": "section:insider#series_12m",
                })
    for d in rebalance_dates:
        markers.append({
            "date": d.isoformat(),
            "type": "rebalance",
            "label": "tournament rebalance",
            "evidence_ref": "section:model_insight",
        })
    markers = [m for m in markers if m["date"] >= chart_start]
    return sorted(markers, key=lambda m: m["date"])


# ── D48: signal matrix ───────────────────────────────────────────────────────

_MATRIX_SPECS = [
    ("return_5d", "5-day return", lambda c, v: _compute_return(c, 5)[0],
     "short-term momentum"),
    ("return_20d", "20-day return", lambda c, v: _compute_return(c, 20)[0],
     "one-month momentum"),
    ("return_60d", "60-day return", lambda c, v: _compute_return(c, 60)[0],
     "quarter momentum"),
    ("volatility_20d", "20-day volatility", lambda c, v: _compute_volatility(c, 20)[0],
     "recent realized risk"),
    ("drawdown_20d", "20-day drawdown", lambda c, v: _compute_drawdown(c, 20)[0],
     "distance from the recent peak"),
]


def _feature_series(bars: Bars, fn) -> list[float]:
    out = []
    closes, vols = bars.closes, bars.volumes
    for i in range(61, len(closes) + 1):
        v = fn(closes[:i], vols[:i])
        out.append(v if isinstance(v, int | float) else float("nan"))
    return out


def _percentile(series: list[float], value: float) -> float:
    clean = sorted(x for x in series if x == x)  # drop NaN
    if not clean:
        return 0.0
    pos = bisect_left(clean, value)
    return round(pos / len(clean), 4)


def signal_matrix(bars: Bars, flat_features: dict) -> list[dict]:
    """Rows for every matrix spec + passthrough rows for remaining computed
    features (news/sentiment etc.) that have no rolling history here."""
    rows: list[dict] = []
    have_history = len(bars.closes) >= 61
    for key, name, fn, read in _MATRIX_SPECS:
        current = (flat_features.get(key) or {}).get("value")
        row = {"key": key, "name": name, "value": current, "read": read}
        if have_history and isinstance(current, int | float):
            series = _feature_series(bars, fn)
            if len(series) >= MIN_PERCENTILE_HISTORY:
                row["percentile"] = _percentile(series[:-1], current)
            else:
                row["percentile"] = None
                row["percentile_note"] = "insufficient history (<1y)"
            spark = [x for x in series[-SPARKLINE_SESSIONS:]]
            row["sparkline"] = [round(x, 6) if x == x else None for x in spark]
        rows.append(row)
    covered = {r["key"] for r in rows}
    for key, blob in flat_features.items():
        if key in covered:
            continue
        rows.append({
            "key": key,
            "name": key.replace("_", " "),
            "value": blob.get("value"),
            "status": blob.get("status"),
            "read": "engine input (no rolling distribution computed)",
        })
    return rows


# ── split visualization ─────────────────────────────────────────────────────


def split_windows(
    state_dates: list[date], splits: list[tuple[int, int]]
) -> list[dict]:
    out = []
    for i, (train_end, val_end) in enumerate(splits):
        if train_end <= 0 or val_end > len(state_dates):
            continue
        out.append({
            "split": i + 1,
            "train": {"start": state_dates[0].isoformat(),
                      "end": state_dates[train_end - 1].isoformat()},
            "validation": {"start": state_dates[train_end].isoformat(),
                           "end": state_dates[val_end - 1].isoformat()},
        })
    return out
