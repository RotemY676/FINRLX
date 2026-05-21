"""Phase W-1 — investor profile schema + seed contract tests.

Verifies:
1. The three tables (``investor_profiles``, ``investor_profile_revisions``,
   ``profile_questions``) are created and writable.
2. ``investor_profiles.user_id`` enforces uniqueness (one current profile
   per user).
3. The seed script is idempotent: running twice inserts the question set
   once, total count stays the same.
4. The seeded catalog covers steps 2-7 (steps 1 + 8 are UI-only).
5. All risk items (step 4) carry valid 1-4 scores in their choices_json.
"""
from __future__ import annotations

import json

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.models.profile import (
    INVESTABLE_BANDS,
    InvestorProfile,
    InvestorProfileRevision,
    ProfileQuestion,
)
from tests.conftest import test_session_factory


@pytest.mark.asyncio
async def test_investor_profile_table_writeable():
    async with test_session_factory() as db:
        profile = InvestorProfile(
            user_id="user-w1-1",
            version=1,
            risk_score=24,
            risk_bucket="moderate",
            horizon_band="3y_5y",
            primary_goal="growth",
            max_drawdown_pct=15.0,
            knowledge_level="intermediate",
            years_investing=4,
            instruments_traded_json=json.dumps(["equities", "etfs"]),
            investable_amount_band="50k_250k",
            income_band="50k_150k",
            liquid_net_worth_band="100k_500k",
            sector_whitelist_json=json.dumps(["Technology"]),
            sector_blacklist_json="[]",
            region_preference="global",
            exclude_leverage=True,
            base_currency="USD",
            trading_frequency="monthly",
            raw_answers_json=json.dumps({"K_01_LEVEL": "intermediate"}),
        )
        db.add(profile)
        await db.commit()

        loaded = (
            await db.execute(
                select(InvestorProfile).where(InvestorProfile.user_id == "user-w1-1")
            )
        ).scalar_one()
        assert loaded.risk_bucket == "moderate"
        assert loaded.max_drawdown_pct == 15.0
        assert json.loads(loaded.sector_whitelist_json) == ["Technology"]


@pytest.mark.asyncio
async def test_investor_profile_user_unique():
    """A user can have at most one current investor_profiles row."""
    async with test_session_factory() as db:
        for _ in range(2):
            db.add(
                InvestorProfile(
                    user_id="user-w1-dup",
                    version=1,
                    risk_score=20,
                    risk_bucket="moderate",
                    horizon_band="1y_3y",
                    primary_goal="growth",
                    max_drawdown_pct=15.0,
                    knowledge_level="novice",
                    investable_amount_band="lt_10k",
                    income_band="lt_50k",
                    liquid_net_worth_band="lt_100k",
                )
            )
        with pytest.raises(IntegrityError):
            await db.commit()
        await db.rollback()


@pytest.mark.asyncio
async def test_profile_revision_appendable():
    """Revisions are append-only — multiple per user/profile are allowed."""
    async with test_session_factory() as db:
        for v in (1, 2, 3):
            db.add(
                InvestorProfileRevision(
                    profile_id="prof-w1-rev",
                    user_id="user-w1-rev",
                    version=v,
                    snapshot_json=json.dumps({"v": v}),
                    change_summary=f"version {v}",
                )
            )
        await db.commit()

        rows = (
            await db.execute(
                select(InvestorProfileRevision)
                .where(InvestorProfileRevision.user_id == "user-w1-rev")
                .order_by(InvestorProfileRevision.version)
            )
        ).scalars().all()
        assert [r.version for r in rows] == [1, 2, 3]


@pytest.mark.asyncio
async def test_seed_profile_questions_idempotent():
    """Running the seed script twice leaves the catalog at the same count."""
    # Override the seed script's session source so it writes to the
    # in-memory test DB rather than the configured engine.
    import scripts.seed_profile_questions as seed_mod
    from scripts.seed_profile_questions import QUESTIONS, seed
    original = seed_mod.async_session_factory
    seed_mod.async_session_factory = test_session_factory
    try:
        first = await seed()
        second = await seed()
    finally:
        seed_mod.async_session_factory = original

    assert first["inserted"] == len(QUESTIONS)
    assert first["skipped"] == 0
    assert second["inserted"] == 0
    assert second["skipped"] == len(QUESTIONS)
    assert first["total_now"] == second["total_now"] == len(QUESTIONS)


@pytest.mark.asyncio
async def test_seeded_catalog_covers_required_steps():
    """Steps 2-7 must each contain at least one question; risk step has 8."""
    async with test_session_factory() as db:
        per_step = (
            await db.execute(
                select(ProfileQuestion.step, func.count())
                .group_by(ProfileQuestion.step)
            )
        ).all()
        counts = {step: n for step, n in per_step}

        assert set(counts.keys()).issuperset({2, 3, 4, 5, 6, 7})
        assert counts[4] == 8, "Risk step must carry exactly 8 Grable-Lytton items"
        assert counts[2] >= 4
        assert counts[3] >= 4
        assert counts[5] >= 3
        assert counts[6] >= 4
        assert counts[7] >= 3


@pytest.mark.asyncio
async def test_risk_items_carry_valid_scores():
    """Every step-4 question's choices must score 1..4 inclusive."""
    async with test_session_factory() as db:
        risk_qs = (
            await db.execute(
                select(ProfileQuestion).where(ProfileQuestion.step == 4)
            )
        ).scalars().all()
        for q in risk_qs:
            choices = json.loads(q.choices_json)
            scores = sorted(c["score"] for c in choices)
            assert scores == [1, 2, 3, 4], (
                f"{q.code} must score 1..4, got {scores}"
            )


def test_band_enums_are_stable():
    """Bands referenced by the wizard frontend must not be renamed silently."""
    assert "lt_10k" in INVESTABLE_BANDS
    assert "gt_1m" in INVESTABLE_BANDS
    assert len(INVESTABLE_BANDS) == 5
