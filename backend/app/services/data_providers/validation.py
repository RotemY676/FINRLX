"""Provider-agnostic OHLCV bar validation (Phase MVP-2).

Functions in this module operate on the standard bar dict shape used by all
data providers. They do not depend on any specific provider package, so they
can be reused by future providers (Alpha Vantage, Polygon, Alpaca, etc).
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any


def validate_bar(bar: dict[str, Any]) -> list[str]:
    """Return a list of quality warnings for a single bar. Empty list = clean."""
    warnings: list[str] = []
    o, h, l, c = bar["open"], bar["high"], bar["low"], bar["close"]
    v = bar["volume"]

    if not (l <= o <= h):
        warnings.append(f"open {o} outside [low {l}, high {h}]")
    if not (l <= c <= h):
        warnings.append(f"close {c} outside [low {l}, high {h}]")
    if l > h:
        warnings.append(f"low {l} > high {h}")
    if any(x is None for x in (o, h, l, c)):
        warnings.append("missing OHLC value")
    if v is None or v < 0:
        warnings.append(f"invalid volume {v}")
    if any(x is not None and x <= 0 for x in (o, h, l, c)):
        warnings.append("non-positive OHLC value")
    return warnings


def detect_gaps(bars: list[dict[str, Any]]) -> list[str]:
    """Detect missing trading days within a bar series.

    A gap is a weekday (Mon-Fri) that falls between min(bar_date) and
    max(bar_date) but has no bar. Holiday calendars are not modeled here;
    a holiday will surface as a gap warning. Acceptable for MVP-2 — the
    operator reviews the warning and confirms whether it's a real gap.
    """
    if len(bars) < 2:
        return []
    by_date = {b["bar_date"]: b for b in bars}
    min_d = min(by_date)
    max_d = max(by_date)
    gaps: list[str] = []
    d = min_d + timedelta(days=1)
    while d < max_d:
        if d.weekday() < 5 and d not in by_date:
            gaps.append(d.isoformat())
        d += timedelta(days=1)
    return gaps


def detect_stale_ticks(bars: list[dict[str, Any]]) -> list[str]:
    """A stale tick is a bar whose OHLCV exactly equals the previous trading day's.

    Real markets virtually never produce identical bars; an exact match almost
    always indicates a vendor cache bug or stale-feed loop.
    """
    if len(bars) < 2:
        return []
    sorted_bars = sorted(bars, key=lambda b: b["bar_date"])
    stale: list[str] = []
    for prev, cur in zip(sorted_bars, sorted_bars[1:]):
        if (
            prev["open"] == cur["open"]
            and prev["high"] == cur["high"]
            and prev["low"] == cur["low"]
            and prev["close"] == cur["close"]
            and prev["volume"] == cur["volume"]
        ):
            stale.append(cur["bar_date"].isoformat())
    return stale
