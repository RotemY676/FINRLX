"""Program LEAP F1.5 — equity price freshness watchdog contract (D6)."""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import delete, select

from app.models.ingestion import MarketBar
from app.models.ops import Incident
from app.services.price_freshness import (
    INCIDENT_TITLE_PREFIX,
    classify_lag,
    emit_incidents_if_degraded,
    evaluate_price_freshness,
)

# Wednesday 2026-06-10 14:00 UTC — a mid-week anchor with no weekend edge.
NOW = datetime(2026, 6, 10, 14, 0, tzinfo=UTC)


def _bar(ticker: str, bar_date: date, quality_flag: str | None = None) -> MarketBar:
    return MarketBar(
        asset_id=f"asset-{ticker}",
        ticker=ticker,
        bar_date=bar_date,
        interval="1d",
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        volume=1_000_000,
        source="chain",
        quality_flag=quality_flag,
    )


async def _reset(db) -> None:
    await db.execute(delete(MarketBar))
    await db.execute(
        delete(Incident).where(Incident.title.like(f"{INCIDENT_TITLE_PREFIX}%"))
    )
    await db.commit()


def test_classify_lag_thresholds_match_d6():
    assert classify_lag(0) == "fresh"
    assert classify_lag(1) == "fresh"
    assert classify_lag(2) == "stale"
    assert classify_lag(5) == "stale"
    assert classify_lag(6) == "degraded"


@pytest.mark.asyncio
async def test_fresh_stale_degraded_classification():
    from tests.conftest import test_session_factory

    async with test_session_factory() as db:
        await _reset(db)
        db.add(_bar("FRESH1", date(2026, 6, 9)))    # 1 trading day behind Wed 10th
        db.add(_bar("STALE1", date(2026, 6, 5)))    # Fri -> lag 3 (Mon,Tue,Wed)
        db.add(_bar("DEGR1", date(2026, 5, 29)))    # lag 8
        await db.commit()
        report = await evaluate_price_freshness(db, now=NOW)
        await _reset(db)

    by = {t.ticker: t for t in report.tickers}
    assert report.expected_latest_session_iso == "2026-06-10"
    assert by["FRESH1"].status == "fresh" and by["FRESH1"].lag_trading_days == 1
    assert by["STALE1"].status == "stale" and by["STALE1"].lag_trading_days == 3
    assert by["DEGR1"].status == "degraded" and by["DEGR1"].lag_trading_days == 8
    assert [t.ticker for t in report.degraded] == ["DEGR1"]


@pytest.mark.asyncio
async def test_weekend_does_not_count_as_lag():
    from tests.conftest import test_session_factory

    # Sunday evening: Friday's bar must be fresh (lag 0).
    sunday = datetime(2026, 6, 7, 20, 0, tzinfo=UTC)
    async with test_session_factory() as db:
        await _reset(db)
        db.add(_bar("WKND", date(2026, 6, 5)))
        await db.commit()
        report = await evaluate_price_freshness(db, now=sunday)
        await _reset(db)
    assert report.expected_latest_session_iso == "2026-06-05"
    assert report.tickers[0].status == "fresh"
    assert report.tickers[0].lag_trading_days == 0


@pytest.mark.asyncio
async def test_quality_flagged_bars_do_not_count_as_freshness():
    from tests.conftest import test_session_factory

    async with test_session_factory() as db:
        await _reset(db)
        db.add(_bar("FLAGD", date(2026, 5, 29)))  # good but old -> degraded
        db.add(_bar("FLAGD", date(2026, 6, 10), quality_flag="suspect_move"))
        await db.commit()
        report = await evaluate_price_freshness(db, now=NOW)
        await _reset(db)
    assert report.tickers[0].status == "degraded"
    assert report.tickers[0].latest_bar_date_iso == "2026-05-29"


@pytest.mark.asyncio
async def test_incident_emission_is_idempotent():
    from tests.conftest import test_session_factory

    async with test_session_factory() as db:
        await _reset(db)
        db.add(_bar("DEGR2", date(2026, 5, 20)))
        await db.commit()
        report = await evaluate_price_freshness(db, now=NOW)
        first = await emit_incidents_if_degraded(db, report)
        second = await emit_incidents_if_degraded(db, report)
        await db.commit()
        rows = (
            await db.execute(
                select(Incident).where(Incident.title == f"{INCIDENT_TITLE_PREFIX}DEGR2")
            )
        ).scalars().all()
        await _reset(db)
    assert first == 1 and second == 0
    assert len(rows) == 1
    assert rows[0].source == "price_freshness"
    assert "lag" in (rows[0].description or "")
