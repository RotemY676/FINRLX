"""Phase FX-4 — FX freshness watchdog contract."""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import delete, select

from app.models.fx import FxRate
from app.models.ops import Incident
from app.services.fx_freshness import (
    INCIDENT_TITLE_PREFIX,
    PairFreshness,
    emit_incidents_if_stale,
    evaluate_freshness,
)


async def _clear_fx_and_incidents(db) -> None:
    """Local cleanup so each test starts from a known baseline."""
    await db.execute(delete(FxRate))
    await db.execute(
        delete(Incident).where(Incident.title.like(f"{INCIDENT_TITLE_PREFIX}%"))
    )
    await db.commit()


@pytest.mark.asyncio
async def test_evaluate_reports_zero_pairs_when_cache_empty():
    from tests.conftest import test_session_factory

    async with test_session_factory() as db:
        await _clear_fx_and_incidents(db)
        report = await evaluate_freshness(db, threshold_hours=24)
    assert report.pairs == []
    assert report.stale_pairs == []


@pytest.mark.asyncio
async def test_evaluate_flags_stale_when_row_older_than_threshold():
    from tests.conftest import test_session_factory

    now = datetime(2025, 6, 10, 12, 0, tzinfo=UTC)
    async with test_session_factory() as db:
        await _clear_fx_and_incidents(db)
        # Fresh row (yesterday) and a very stale one (10 days ago)
        db.add(
            FxRate(
                base_currency="USD", quote_currency="EUR",
                rate_date=(now - timedelta(days=1)).date(),
                rate=0.92, source="frankfurter",
            )
        )
        db.add(
            FxRate(
                base_currency="USD", quote_currency="ILS",
                rate_date=(now - timedelta(days=10)).date(),
                rate=3.70, source="frankfurter",
            )
        )
        await db.commit()
        report = await evaluate_freshness(db, threshold_hours=48, now=now)

    fresh = next(p for p in report.pairs if p.quote == "EUR")
    stale = next(p for p in report.pairs if p.quote == "ILS")
    assert fresh.is_stale is False
    assert stale.is_stale is True
    assert stale in report.stale_pairs


@pytest.mark.asyncio
async def test_evaluate_picks_most_recent_row_per_pair():
    from tests.conftest import test_session_factory

    now = datetime(2025, 6, 15, 12, 0, tzinfo=UTC)
    async with test_session_factory() as db:
        await _clear_fx_and_incidents(db)
        # Two USD->EUR rows; the newer one wins
        db.add(
            FxRate(
                base_currency="USD", quote_currency="EUR",
                rate_date=date(2025, 6, 5), rate=0.91, source="frankfurter",
            )
        )
        db.add(
            FxRate(
                base_currency="USD", quote_currency="EUR",
                rate_date=date(2025, 6, 13), rate=0.92, source="frankfurter",
            )
        )
        await db.commit()
        report = await evaluate_freshness(db, threshold_hours=72, now=now)

    eur = next(p for p in report.pairs if p.quote == "EUR")
    assert eur.latest_rate_date_iso == "2025-06-13"
    assert eur.is_stale is False  # 2 days old, threshold 72h


@pytest.mark.asyncio
async def test_emit_incidents_opens_one_per_stale_pair():
    from tests.conftest import test_session_factory

    now = datetime(2025, 7, 1, 12, 0, tzinfo=UTC)
    async with test_session_factory() as db:
        await _clear_fx_and_incidents(db)
        # Insert 2 stale pairs (10 days old) → both should fire
        for quote in ("EUR", "ILS"):
            db.add(
                FxRate(
                    base_currency="USD", quote_currency=quote,
                    rate_date=(now - timedelta(days=10)).date(),
                    rate=1.0, source="frankfurter",
                )
            )
        await db.commit()
        report = await evaluate_freshness(db, threshold_hours=48, now=now)
        result = await emit_incidents_if_stale(db, report)

        incidents = (
            await db.execute(
                select(Incident).where(
                    Incident.title.like(f"{INCIDENT_TITLE_PREFIX}%")
                )
            )
        ).scalars().all()

    assert result["opened"] == 2
    assert result["skipped_existing"] == 0
    assert len(incidents) == 2


@pytest.mark.asyncio
async def test_emit_incidents_is_idempotent_on_re_run():
    """Running the watchdog twice doesn't double-open incidents."""
    from tests.conftest import test_session_factory

    now = datetime(2025, 8, 1, 12, 0, tzinfo=UTC)
    async with test_session_factory() as db:
        await _clear_fx_and_incidents(db)
        db.add(
            FxRate(
                base_currency="USD", quote_currency="EUR",
                rate_date=(now - timedelta(days=10)).date(),
                rate=0.92, source="frankfurter",
            )
        )
        await db.commit()
        report = await evaluate_freshness(db, threshold_hours=48, now=now)
        first = await emit_incidents_if_stale(db, report)
        second = await emit_incidents_if_stale(db, report)
        incidents = (
            await db.execute(
                select(Incident).where(
                    Incident.title.like(f"{INCIDENT_TITLE_PREFIX}%")
                )
            )
        ).scalars().all()

    assert first["opened"] == 1
    assert second["opened"] == 0
    assert second["skipped_existing"] == 1
    assert len(incidents) == 1


@pytest.mark.asyncio
async def test_severity_scales_with_age():
    """Old (>7d) is critical (sev 1); 3-7d is high (sev 2); <72h is warning (sev 3)."""
    from app.services.fx_freshness import _severity_for

    assert _severity_for(48) == 3
    assert _severity_for(72) == 3
    assert _severity_for(96) == 2  # 4 days
    assert _severity_for(168) == 2  # 7 days
    assert _severity_for(200) == 1


def test_pair_freshness_is_frozen():
    """A PairFreshness row is immutable post-construction (dataclass frozen)."""
    p = PairFreshness(
        base="USD", quote="EUR",
        latest_rate_date_iso="2025-01-01",
        age_hours=10.0, is_stale=False,
    )
    with pytest.raises(Exception):
        p.is_stale = True  # type: ignore[misc]
