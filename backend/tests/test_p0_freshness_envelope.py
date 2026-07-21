"""US-P0-07 — freshness is declared in the response envelope (meta.freshness).

`meta.freshness` was defined but never populated, so every response implicitly
read as fresh. These tests cover the reusable builder and its first wiring on
the canonical live-price surface (/pricechart): a served chart declares the age
of its newest session, and a chart with no data is stale, never silently fresh.
"""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from app.services.freshness_state import freshness_state_from_latest
from app.utils import trading_calendar


def test_none_latest_is_stale_with_no_timestamp():
    fs = freshness_state_from_latest(None)
    assert fs.is_stale is True
    assert fs.data_as_of is None
    assert fs.staleness_reason and "no market data" in fs.staleness_reason


def test_latest_equal_expected_is_fresh():
    now = datetime(2026, 7, 21, 15, 0, tzinfo=UTC)
    expected = trading_calendar.expected_latest_session(now)
    fs = freshness_state_from_latest(expected, now=now)
    assert fs.is_stale is False
    assert fs.staleness_reason is None
    assert fs.data_as_of is not None and fs.data_as_of.tzinfo is not None


def test_far_past_latest_is_stale_with_reason():
    now = datetime(2026, 7, 21, 15, 0, tzinfo=UTC)
    expected = trading_calendar.expected_latest_session(now)
    old = expected - timedelta(days=40)
    fs = freshness_state_from_latest(old, now=now)
    assert fs.is_stale is True
    assert fs.staleness_reason and "behind expected" in fs.staleness_reason
    assert fs.data_as_of == datetime(old.year, old.month, old.day, tzinfo=UTC)


@pytest.mark.asyncio
async def test_pricechart_populates_meta_freshness(client, monkeypatch):
    """A served chart declares freshness; old fixture bars → is_stale True."""
    import app.api.v1.pricechart as pc
    import app.services.single_ticker_analysis as sta
    from app.services.single_ticker_analysis import Bars

    dates, closes, d = [], [], date(2024, 6, 3)
    while len(dates) < 60:
        if d.weekday() < 5:
            dates.append(d)
            closes.append(100.0 + len(dates))
        d += timedelta(days=1)
    bars = Bars(dates=dates, closes=closes, volumes=[1_000_000] * 60,
                highs=[c * 1.01 for c in closes], lows=[c * 0.99 for c in closes])

    def fake_history(sym, days):
        if sym == "SPY":
            raise RuntimeError("no benchmark")
        return bars

    monkeypatch.setattr(sta, "fetch_history", fake_history)
    pc._cache.clear()
    meta = (await client.get("/api/v1/pricechart?ticker=FRSHT")).json()["meta"]
    assert meta["freshness"] is not None, "meta.freshness must be populated"
    assert meta["freshness"]["is_stale"] is True  # 2024 bars are far behind 2026
    assert meta["freshness"]["data_as_of"] is not None


@pytest.mark.asyncio
async def test_pricechart_no_data_is_stale_not_silently_fresh(client, monkeypatch):
    import app.api.v1.pricechart as pc
    import app.services.single_ticker_analysis as sta

    def no_data(sym, days):
        raise RuntimeError("providers down")

    monkeypatch.setattr(sta, "fetch_history", no_data)
    pc._cache.clear()
    body = (await client.get("/api/v1/pricechart?ticker=ZZZQ")).json()
    assert body["data"] is None
    assert body["meta"]["freshness"]["is_stale"] is True
