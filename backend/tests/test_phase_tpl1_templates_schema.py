"""Phase TPL-1 — recommendation_templates schema + seed contract.

Coverage:
* The table is writeable; key UNIQUE constraint holds.
* Seed script is idempotent.
* All 5 seed templates exist with the right keys.
* Each seed maps cleanly through derive_allocation (no orphan bucket).
* Each seed's allocation_summary matches what the W-4 mapping produces.
"""
from __future__ import annotations

import json

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.recommendation_template import (
    TEMPLATE_KEYS,
    RecommendationTemplate,
)
from app.services.profile_mapping import derive_allocation
from tests.conftest import test_session_factory


@pytest.mark.asyncio
async def test_template_table_writeable():
    async with test_session_factory() as db:
        db.add(
            RecommendationTemplate(
                key="user-test-1",
                name="User Test 1",
                description="A simple test template",
                badge="Moderate",
                risk_bucket="moderate",
                horizon_band="3y_5y",
                primary_goal="growth",
                max_drawdown_pct=15.0,
                sector_whitelist_json=json.dumps([]),
                sector_blacklist_json=json.dumps([]),
                exclude_leverage=True,
                base_currency="USD",
                trading_frequency="monthly",
                region_preference="global",
                is_seed=False,
                is_active=True,
            )
        )
        await db.commit()

        loaded = (
            await db.execute(
                select(RecommendationTemplate).where(
                    RecommendationTemplate.key == "user-test-1"
                )
            )
        ).scalar_one()
        assert loaded.name == "User Test 1"
        assert loaded.is_seed is False


@pytest.mark.asyncio
async def test_template_key_unique():
    async with test_session_factory() as db:
        for _ in range(2):
            db.add(
                RecommendationTemplate(
                    key="dup-key",
                    name="dup",
                    description="dup",
                    badge="Moderate",
                    risk_bucket="moderate",
                    horizon_band="3y_5y",
                    primary_goal="growth",
                    max_drawdown_pct=15.0,
                )
            )
        with pytest.raises(IntegrityError):
            await db.commit()
        await db.rollback()


@pytest.mark.asyncio
async def test_seed_recommendation_templates_idempotent():
    """Running the seed script twice leaves the catalog at the same count."""
    import scripts.seed_recommendation_templates as seed_mod
    from scripts.seed_recommendation_templates import SEED_TEMPLATES, seed

    original = seed_mod.async_session_factory
    seed_mod.async_session_factory = test_session_factory
    try:
        first = await seed()
        second = await seed()
    finally:
        seed_mod.async_session_factory = original

    assert first["inserted"] == len(SEED_TEMPLATES)
    assert first["skipped"] == 0
    assert second["inserted"] == 0
    assert second["skipped"] == len(SEED_TEMPLATES)
    assert first["total_now"] >= len(SEED_TEMPLATES)


@pytest.mark.asyncio
async def test_all_five_seed_keys_present():
    async with test_session_factory() as db:
        rows = (
            await db.execute(
                select(RecommendationTemplate.key).where(
                    RecommendationTemplate.is_seed
                )
            )
        ).scalars().all()
        keys = set(rows)
    assert set(TEMPLATE_KEYS).issubset(keys)


@pytest.mark.asyncio
async def test_every_seed_template_maps_to_a_known_allocation():
    """Bucket + horizon for each seed must be a valid (bucket, horizon) pair."""
    async with test_session_factory() as db:
        seeds = (
            await db.execute(
                select(RecommendationTemplate).where(
                    RecommendationTemplate.is_seed
                )
            )
        ).scalars().all()
        for t in seeds:
            # Should not raise
            allocation = derive_allocation(t.risk_bucket, t.horizon_band)
            # allocation_summary is "<equity>/<defensive>"
            expected = f"{int(round(allocation.equity_pct))}/{int(round(allocation.defensive_pct))}"
            assert t.allocation_summary == expected, (
                f"{t.key}: allocation_summary={t.allocation_summary!r} != {expected!r}"
            )


@pytest.mark.asyncio
async def test_tech_growth_carries_tech_sector_whitelist():
    async with test_session_factory() as db:
        t = (
            await db.execute(
                select(RecommendationTemplate).where(
                    RecommendationTemplate.key == "tech_growth"
                )
            )
        ).scalar_one()
    whitelist = json.loads(t.sector_whitelist_json)
    assert "Technology" in whitelist
    assert t.risk_bucket == "aggressive"


@pytest.mark.asyncio
async def test_income_focus_carries_dividend_sectors():
    async with test_session_factory() as db:
        t = (
            await db.execute(
                select(RecommendationTemplate).where(
                    RecommendationTemplate.key == "income_focus"
                )
            )
        ).scalar_one()
    whitelist = json.loads(t.sector_whitelist_json)
    assert "Financials" in whitelist
    assert "Utilities" in whitelist
    assert t.primary_goal == "income"
