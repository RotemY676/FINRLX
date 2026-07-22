"""US-P0-07 — freshness is declared in the response envelope (meta.freshness).

`meta.freshness` was defined but never populated, so every response implicitly
read as fresh. These tests cover the reusable builder and its first wiring on
the canonical live-price surface (/pricechart): a served chart declares the age
of its newest session, and a chart with no data is stale, never silently fresh.
"""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from app.services.freshness_state import (
    freshness_state_from_datetime,
    freshness_state_from_dossier,
    freshness_state_from_latest,
)
from app.utils import trading_calendar


def _bars(n=420):
    """Weekday bars ending well in the past, so served dossiers read stale."""
    from app.services.single_ticker_analysis import Bars

    dates, closes = [], []
    d, px, i = date(2024, 1, 1), 100.0, 0
    while len(dates) < n:
        if d.weekday() < 5:
            px *= 1.0 + (0.004 if (i // 20) % 2 == 0 else -0.002)
            dates.append(d)
            closes.append(round(px, 4))
            i += 1
        d += timedelta(days=1)
    return Bars(dates=dates, closes=closes, volumes=[1_000_000] * n,
                highs=[c * 1.01 for c in closes], lows=[c * 0.99 for c in closes])


@pytest.fixture
def stubbed_dossier(monkeypatch):
    """Build dossiers from fixture bars with no network access."""
    import app.services.data_providers.finnhub_extras as fx
    import app.services.data_providers.sec_xbrl as x
    from app.services import autopilot

    bars = _bars(420)
    monkeypatch.setattr(autopilot, "fetch_history", lambda s, days: bars)
    monkeypatch.setattr(autopilot, "fetch_news", lambda s, limit=20: ([], False))
    monkeypatch.setattr(x, "resolve_cik", lambda t: None)
    monkeypatch.setattr(fx, "_key", lambda: None)
    autopilot._dossier_cache.clear()
    return bars


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


# ── i2: the remaining served surfaces ──────────────────────────────────────
#
# i1 wired /pricechart only. Every other surface still answered with
# meta.freshness == null, i.e. implicitly fresh. These cover the builders for
# the two other shapes of "newest data" the codebase stores (a datetime
# data_as_of on recommendations, a latest_bar string inside a dossier) and the
# five endpoints that serve them.


def test_from_datetime_none_is_stale():
    fs = freshness_state_from_datetime(None)
    assert fs.is_stale is True
    assert fs.data_as_of is None


def test_from_datetime_uses_the_date_component():
    now = datetime(2026, 7, 21, 15, 0, tzinfo=UTC)
    expected = trading_calendar.expected_latest_session(now)
    moment = datetime(expected.year, expected.month, expected.day, 20, 30, tzinfo=UTC)
    fs = freshness_state_from_datetime(moment, now=now)
    assert fs.is_stale is False


def test_from_dossier_reads_latest_bar():
    now = datetime(2026, 7, 21, 15, 0, tzinfo=UTC)
    expected = trading_calendar.expected_latest_session(now)
    fs = freshness_state_from_dossier(
        {"freshness": {"latest_bar": expected.isoformat(), "bars": 400}}, now=now
    )
    assert fs.is_stale is False
    assert fs.data_as_of is not None


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        {"freshness": None},
        {"freshness": {}},
        {"freshness": {"latest_bar": None}},
        {"freshness": {"latest_bar": "not-a-date"}},
        {"freshness": "malformed"},
    ],
)
def test_from_dossier_fails_closed_on_missing_or_bad_latest_bar(payload):
    """A malformed dossier must never be served as fresh."""
    fs = freshness_state_from_dossier(payload)
    assert fs.is_stale is True
    assert fs.data_as_of is None


async def _age_the_served_recommendation(stamped: datetime) -> None:
    """Backdate the seeded published recommendation's data_as_of.

    The test DB ships a freshly-stamped recommendation, so staleness is
    exercised by ageing that row rather than inserting one (Recommendation
    requires a universe_id FK).
    """
    from sqlalchemy import select

    from app.models.recommendation import Recommendation
    from tests.conftest import test_session_factory as async_session_maker

    async with async_session_maker() as db:
        rows = (await db.execute(
            select(Recommendation).where(Recommendation.context != "backtest")
        )).scalars().all()
        assert rows, "fixture expects at least one seeded recommendation"
        for row in rows:
            row.data_as_of = stamped
        await db.commit()


@pytest.mark.asyncio
async def test_overview_declares_freshness(client):
    """/overview must declare the age of the recommendation it served."""
    meta = (await client.get("/api/v1/overview")).json()["meta"]
    assert meta["freshness"] is not None, "meta.freshness must be populated"


@pytest.mark.asyncio
async def test_recommendations_current_declares_freshness(client):
    body = (await client.get("/api/v1/recommendations/current")).json()
    fs = body["meta"]["freshness"]
    assert fs is not None, "meta.freshness must be populated"
    if body["data"] and body["data"].get("data_as_of"):
        # The envelope must describe the SAME data the body carries.
        assert fs["data_as_of"][:10] == body["data"]["data_as_of"][:10]


@pytest.mark.asyncio
async def test_recommendations_current_reports_stored_data_as_of(client):
    """A served recommendation declares the age of ITS data, not "now"."""
    await _age_the_served_recommendation(datetime(2024, 6, 3, 21, 0, tzinfo=UTC))

    body = (await client.get("/api/v1/recommendations/current")).json()
    fs = body["meta"]["freshness"]
    assert fs is not None
    assert fs["is_stale"] is True, "2024 data served in 2026 must read stale"
    assert fs["data_as_of"].startswith("2024-06-03")


@pytest.mark.asyncio
async def test_overview_reports_stored_data_as_of(client):
    await _age_the_served_recommendation(datetime(2024, 6, 3, 21, 0, tzinfo=UTC))

    meta = (await client.get("/api/v1/overview")).json()["meta"]
    assert meta["freshness"]["is_stale"] is True
    assert meta["freshness"]["data_as_of"].startswith("2024-06-03")


@pytest.mark.asyncio
async def test_autopilot_dossier_declares_freshness(client, stubbed_dossier):
    body = (await client.get("/api/v1/autopilot/dossier?ticker=FRZ1")).json()
    fs = body["meta"]["freshness"]
    assert fs is not None, "dossier envelope must declare freshness"
    assert fs["is_stale"] is True  # fixture bars end in 2024/2025
    # The envelope must agree with the dossier's own domain freshness block.
    assert fs["data_as_of"].startswith(body["data"]["freshness"]["latest_bar"])


@pytest.mark.asyncio
async def test_desk_section_declares_freshness(client, stubbed_dossier):
    body = (await client.get("/api/v1/autopilot/desk/FRZ2/chart")).json()
    assert body["data"]["section"] == "chart"
    assert body["meta"]["freshness"]["is_stale"] is True


@pytest.mark.asyncio
async def test_desk_status_declares_freshness_and_etag_tracks_staleness(
    client, stubbed_dossier
):
    """The dials declare their age, and a stale reading cannot hide behind 304."""
    await client.get("/api/v1/autopilot/dossier?ticker=FRZ3")  # persist one

    r = await client.get("/api/v1/autopilot/desk/FRZ3/status")
    assert r.status_code == 200
    assert r.json()["meta"]["freshness"]["is_stale"] is True
    etag = r.headers["ETag"]
    assert "stale" in etag, "staleness must participate in the ETag"

    # Same ETag still revalidates to 304 (no behaviour regression).
    again = await client.get(
        "/api/v1/autopilot/desk/FRZ3/status", headers={"If-None-Match": etag}
    )
    assert again.status_code == 304

    # A pre-US-P0-07 ETag (fingerprint only) must NOT match, so a client
    # holding a cached "fresh" reading is forced to re-fetch.
    legacy = etag.replace("-stale", "")
    forced = await client.get(
        "/api/v1/autopilot/desk/FRZ3/status", headers={"If-None-Match": legacy}
    )
    assert forced.status_code == 200
