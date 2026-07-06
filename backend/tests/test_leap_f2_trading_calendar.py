"""Program LEAP F2 — trading calendar property tests (gate G3.1)."""
from __future__ import annotations

from datetime import UTC, date, datetime

from app.utils import trading_calendar as tc


def test_backend_is_real_calendar_not_fallback():
    assert tc.CALENDAR_BACKEND == "exchange_calendars"


def test_weekend_is_not_a_session():
    assert tc.is_session(date(2026, 6, 6)) is False  # Saturday
    assert tc.is_session(date(2026, 6, 7)) is False  # Sunday
    assert tc.is_session(date(2026, 6, 8)) is True   # Monday


def test_us_holidays_excluded():
    assert tc.is_session(date(2026, 7, 3)) is False   # Independence Day observed
    assert tc.is_session(date(2026, 11, 26)) is False # Thanksgiving
    assert tc.is_session(date(2026, 12, 25)) is False # Christmas
    assert tc.is_session(date(2026, 4, 3)) is False   # Good Friday


def test_sessions_in_range_spans_holiday_and_weekend():
    got = tc.sessions_in_range(date(2026, 7, 1), date(2026, 7, 6))
    assert got == [date(2026, 7, 1), date(2026, 7, 2), date(2026, 7, 6)]


def test_year_boundary():
    got = tc.sessions_in_range(date(2025, 12, 30), date(2026, 1, 5))
    assert date(2026, 1, 1) not in got
    assert date(2025, 12, 31) in got and date(2026, 1, 2) in got


def test_previous_session_over_long_weekend():
    # Monday 2026-07-06 back over the July-3 holiday + weekend -> Thursday 07-02
    assert tc.previous_session(date(2026, 7, 6)) == date(2026, 7, 2)
    assert tc.previous_session(date(2026, 7, 6), inclusive=True) == date(2026, 7, 6)


def test_expected_latest_session_holiday_aware():
    # Saturday July 4th evening: newest expected bar is Thursday July 2nd
    now = datetime(2026, 7, 4, 20, 0, tzinfo=UTC)
    assert tc.expected_latest_session(now) == date(2026, 7, 2)
    # Early-morning grace: 05:00 UTC on a Tuesday still expects Friday-…-Monday? No:
    # anchor shifts to Monday, which is a session.
    now2 = datetime(2026, 6, 9, 5, 0, tzinfo=UTC)
    assert tc.expected_latest_session(now2) == date(2026, 6, 8)


def test_trading_day_lag_ignores_holidays():
    # Latest bar Thu 2026-07-02, expected Mon 2026-07-06: lag is exactly 1
    # (July 3 holiday + weekend don't count).
    assert tc.trading_day_lag(date(2026, 7, 2), date(2026, 7, 6)) == 1
    assert tc.trading_day_lag(date(2026, 7, 6), date(2026, 7, 6)) == 0
