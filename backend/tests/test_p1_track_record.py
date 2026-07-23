"""Phase 7 — the forward-scored track record.

Determinism proves the same inputs give the same answer twice; it says nothing
about whether the answer was good. This is the other half, and its honesty
rests on refusing to report early: a hit rate over a handful of observations is
noise wearing a percentage sign.
"""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from app.models.track_record import StanceObservation
from app.services.track_record import (
    MIN_SAMPLE_FOR_RATE,
    record_stance,
    score_matured,
    track_record_summary,
)
from tests.conftest import test_session_factory as AsyncSessionLocal

BASE = date(2026, 1, 5)


async def _clear():
    from sqlalchemy import delete

    async with AsyncSessionLocal() as db:
        await db.execute(delete(StanceObservation))
        await db.commit()


@pytest.mark.asyncio
async def test_records_what_was_claimed_at_the_moment_it_was_claimed():
    await _clear()
    async with AsyncSessionLocal() as db:
        row = await record_stance(
            db, ticker="AAA", stance="buy", composite_score=0.42,
            observed_bar_date=BASE, observed_close=100.0,
            avg_confidence=0.7, uncertainty_tier="low", config_version="v1",
        )
        await db.commit()
    assert row is not None
    assert row.observed_close == 100.0
    # Not yet knowable — must be NULL, never 0, which would read as a flat outcome.
    assert row.realized_return is None
    assert row.scored_at is None


@pytest.mark.asyncio
async def test_refreshing_a_dossier_does_not_manufacture_predictions():
    """Dedupe keeps this a record of claims, not of page views."""
    await _clear()
    async with AsyncSessionLocal() as db:
        first = await record_stance(
            db, ticker="BBB", stance="buy", composite_score=0.4,
            observed_bar_date=BASE, observed_close=50.0,
        )
        await db.commit()
        second = await record_stance(
            db, ticker="BBB", stance="buy", composite_score=0.4,
            observed_bar_date=BASE, observed_close=50.0,
        )
        await db.commit()
    assert first is not None
    assert second is None, "a second observation inside the window inflates the sample"


@pytest.mark.asyncio
async def test_only_scores_once_the_horizon_has_actually_elapsed():
    await _clear()
    async with AsyncSessionLocal() as db:
        await record_stance(
            db, ticker="CCC", stance="buy", composite_score=0.4,
            observed_bar_date=BASE, observed_close=100.0, horizon_days=21,
        )
        await db.commit()

    def lookup(_ticker, _on_or_after):
        return (BASE + timedelta(days=21), 110.0)

    async with AsyncSessionLocal() as db:
        # One day short of the horizon — nothing may be scored.
        assert await score_matured(db, lookup, today=BASE + timedelta(days=20)) == 0
        await db.commit()
    async with AsyncSessionLocal() as db:
        assert await score_matured(db, lookup, today=BASE + timedelta(days=21)) == 1
        await db.commit()

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        row = (await db.execute(select(StanceObservation).where(StanceObservation.ticker == "CCC"))).scalar_one()
    assert row.realized_return == pytest.approx(0.10)


@pytest.mark.asyncio
async def test_an_unobservable_outcome_is_left_unscored_not_imputed():
    await _clear()
    async with AsyncSessionLocal() as db:
        await record_stance(
            db, ticker="DDD", stance="buy", composite_score=0.4,
            observed_bar_date=BASE, observed_close=100.0, horizon_days=5,
        )
        await db.commit()

    async with AsyncSessionLocal() as db:
        scored = await score_matured(db, lambda *_: None, today=BASE + timedelta(days=30))
        await db.commit()
    assert scored == 0, "a missing outcome price must leave the row unscored"


@pytest.mark.asyncio
async def test_withholds_a_hit_rate_on_a_thin_sample():
    await _clear()
    async with AsyncSessionLocal() as db:
        for i in range(3):
            await record_stance(
                db, ticker=f"T{i}", stance="buy", composite_score=0.4,
                observed_bar_date=BASE, observed_close=100.0, horizon_days=1,
            )
        await db.commit()
    async with AsyncSessionLocal() as db:
        await score_matured(db, lambda *_: (BASE + timedelta(days=1), 105.0),
                            today=BASE + timedelta(days=10))
        await db.commit()

    async with AsyncSessionLocal() as db:
        summary = await track_record_summary(db)
    assert summary["status"] == "insufficient_sample"
    assert summary["hit_rate"] is None
    assert str(MIN_SAMPLE_FOR_RATE) in summary["note"]


@pytest.mark.asyncio
async def test_reports_a_rate_once_the_sample_clears_the_floor():
    await _clear()
    n = MIN_SAMPLE_FOR_RATE + 4
    async with AsyncSessionLocal() as db:
        for i in range(n):
            await record_stance(
                db, ticker=f"S{i}", stance="buy", composite_score=0.4,
                observed_bar_date=BASE, observed_close=100.0, horizon_days=1,
                uncertainty_tier="low",
            )
        await db.commit()

    # Three quarters of them go the right way.
    def lookup(ticker, _on):
        idx = int(ticker[1:])
        return (BASE + timedelta(days=1), 105.0 if idx % 4 else 95.0)

    async with AsyncSessionLocal() as db:
        await score_matured(db, lookup, today=BASE + timedelta(days=10))
        await db.commit()

    async with AsyncSessionLocal() as db:
        summary = await track_record_summary(db)
    assert summary["status"] == "reported"
    assert 0.0 < summary["hit_rate"] <= 1.0
    assert summary["directional_observations"] == n


@pytest.mark.asyncio
async def test_a_neutral_stance_makes_no_directional_claim_and_is_excluded():
    """Counting it either way manufactures a result from an absence of one."""
    await _clear()
    async with AsyncSessionLocal() as db:
        await record_stance(
            db, ticker="NEU", stance="hold", composite_score=0.0,
            observed_bar_date=BASE, observed_close=100.0, horizon_days=1,
        )
        await db.commit()
    async with AsyncSessionLocal() as db:
        await score_matured(db, lambda *_: (BASE + timedelta(days=1), 130.0),
                            today=BASE + timedelta(days=10))
        await db.commit()

    async with AsyncSessionLocal() as db:
        summary = await track_record_summary(db)
    assert summary["observations_scored"] == 1
    assert summary["directional_observations"] == 0


@pytest.mark.asyncio
async def test_an_empty_record_says_so_rather_than_showing_zero():
    await _clear()
    async with AsyncSessionLocal() as db:
        summary = await track_record_summary(db)
    assert summary["observations_recorded"] == 0
    assert summary["hit_rate"] is None
    assert summary["status"] == "insufficient_sample"
    assert "not a backtest" in summary["kind"]
