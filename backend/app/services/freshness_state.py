"""US-P0-07 — build the response-envelope FreshnessState for a served surface.

`meta.freshness` (app/schemas/common.FreshnessState) exists in the response
envelope but was never populated, so every response read as implicitly fresh —
a silent staleness leak. This helper reuses the price-freshness classification
(D6 thresholds via `classify_lag` + the trading calendar) so a display endpoint
can declare the age of what it served instead of leaving the field null.

Pure and DB-free: the caller passes the latest observed session date (e.g. the
last point on a price chart). `None` (no data) is treated as stale, not fresh.
"""
from __future__ import annotations

from datetime import UTC, date, datetime

from app.schemas.common import FreshnessState
from app.services.price_freshness import classify_lag
from app.utils import trading_calendar


def freshness_state_from_latest(
    latest: date | None, now: datetime | None = None
) -> FreshnessState:
    """Return the envelope FreshnessState for data whose newest session is ``latest``."""
    if latest is None:
        return FreshnessState(
            data_as_of=None,
            is_stale=True,
            staleness_reason="no market data available",
        )
    now = now or datetime.now(UTC)
    expected = trading_calendar.expected_latest_session(now)
    lag = trading_calendar.trading_day_lag(latest, expected)
    status = classify_lag(lag)  # fresh | stale | degraded
    is_stale = status != "fresh"
    data_as_of = datetime(latest.year, latest.month, latest.day, tzinfo=UTC)
    reason: str | None = None
    if is_stale:
        reason = (
            f"latest session {latest.isoformat()} is {lag} trading day(s) behind "
            f"expected {expected.isoformat()} ({status})"
        )
    return FreshnessState(
        data_as_of=data_as_of, is_stale=is_stale, staleness_reason=reason
    )
