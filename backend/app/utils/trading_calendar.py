"""Program LEAP F2 — trading calendar utility (decision D3).

Thin wrapper over `exchange_calendars` (XNYS primary) giving the rest of the
codebase four calendar-correct primitives:

    is_session(d)                  -> bool
    sessions_in_range(a, b)        -> list[date]
    previous_session(d)            -> date   (latest session strictly before d,
                                              or d itself if d is a session and
                                              inclusive=True)
    expected_latest_session(now)   -> date   (newest session whose daily bar a
                                              healthy pipeline should have)

Graceful degradation: if exchange_calendars is unavailable at runtime the
module falls back to weekday (Mon-Fri) logic — identical to the pre-F2
behavior — and sets CALENDAR_BACKEND = "weekday-fallback" so callers/tests
can detect the degraded mode. This keeps deployments bootable even if the
dependency is missing, per the plan's never-crash posture.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from functools import lru_cache

DEFAULT_EXCHANGE = "XNYS"
# Daily bars are expected available by this UTC hour on the following day.
INGEST_COMPLETION_HOUR_UTC = 6

try:  # pragma: no cover - exercised via CALENDAR_BACKEND assertions
    import exchange_calendars as _xc

    CALENDAR_BACKEND = "exchange_calendars"
except ImportError:  # pragma: no cover
    _xc = None
    CALENDAR_BACKEND = "weekday-fallback"

__all__ = [
    "CALENDAR_BACKEND",
    "DEFAULT_EXCHANGE",
    "is_session",
    "sessions_in_range",
    "previous_session",
    "expected_latest_session",
    "trading_day_lag",
]


@lru_cache(maxsize=4)
def _calendar(exchange: str):
    if _xc is None:
        return None
    return _xc.get_calendar(exchange)


def is_session(d: date, exchange: str = DEFAULT_EXCHANGE) -> bool:
    cal = _calendar(exchange)
    if cal is None:
        return d.weekday() < 5
    return bool(cal.is_session(d.isoformat()))


def sessions_in_range(
    start: date, end: date, exchange: str = DEFAULT_EXCHANGE
) -> list[date]:
    """All sessions in [start, end] inclusive, ascending."""
    if start > end:
        return []
    cal = _calendar(exchange)
    if cal is None:
        out, d = [], start
        while d <= end:
            if d.weekday() < 5:
                out.append(d)
            d += timedelta(days=1)
        return out
    return [ts.date() for ts in cal.sessions_in_range(start.isoformat(), end.isoformat())]


def previous_session(
    d: date, exchange: str = DEFAULT_EXCHANGE, inclusive: bool = False
) -> date:
    """Latest session strictly before d (or d itself when inclusive and a session)."""
    if inclusive and is_session(d, exchange):
        return d
    probe = d - timedelta(days=1)
    for _ in range(30):  # longest exchange closures are far shorter
        if is_session(probe, exchange):
            return probe
        probe -= timedelta(days=1)
    raise ValueError(f"no session found in the 30 days before {d} on {exchange}")


def expected_latest_session(
    now: datetime, exchange: str = DEFAULT_EXCHANGE
) -> date:
    """Newest session whose daily bar should already be ingested at `now` (UTC)."""
    anchor = now.date()
    if now.hour < INGEST_COMPLETION_HOUR_UTC:
        anchor -= timedelta(days=1)
    return previous_session(anchor, exchange, inclusive=True)


def trading_day_lag(
    latest: date, expected: date, exchange: str = DEFAULT_EXCHANGE
) -> int:
    """Number of sessions in (latest, expected]; 0 when latest >= expected."""
    if latest >= expected:
        return 0
    return len(sessions_in_range(latest + timedelta(days=1), expected, exchange))
