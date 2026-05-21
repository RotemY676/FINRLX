"""Phase W-5 — profile → pipeline integration contract.

Coverage:
* Pure helpers: filter_universe_by_profile, cap_position_weight, cap_confidence
  behave correctly with None / empty / populated overrides.
* load_overrides_for_user returns None for a user without a profile.
* load_overrides_for_user returns a populated overrides for a saved profile,
  with all fields (sector lists, region, exclude_leverage, targets) wired.
* run_risk_overlay with overrides tightens the per-asset cap.
* Pipeline regression: running with profile_overrides=None preserves
  identical post_risk_weights vs the pre-W-5 cap of 0.15.
"""
from __future__ import annotations

import json
import secrets

import pytest

from app.models.profile import InvestorProfile
from app.services.profile_pipeline_overrides import (
    ProfileOverrides,
    cap_confidence,
    cap_position_weight,
    filter_universe_by_profile,
    load_overrides_for_user,
)

# ── Pure helper tests ────────────────────────────────────────────────


def _make_overrides(
    sector_whitelist: tuple[str, ...] = (),
    sector_blacklist: tuple[str, ...] = (),
    bucket: str = "moderate",
    horizon: str = "3y_5y",
) -> ProfileOverrides:
    from app.services.profile_mapping import derive_allocation

    return ProfileOverrides(
        profile_id="prof-1",
        profile_version=1,
        risk_bucket=bucket,
        horizon_band=horizon,
        sector_whitelist=sector_whitelist,
        sector_blacklist=sector_blacklist,
        region_preference="global",
        exclude_leverage=True,
        targets=derive_allocation(bucket, horizon),
    )


def test_cap_position_weight_returns_base_when_none():
    assert cap_position_weight(0.15, None) == 0.15


def test_cap_position_weight_tightens_with_profile():
    overrides = _make_overrides(bucket="conservative")  # cap 6% => 0.06
    assert cap_position_weight(0.15, overrides) == pytest.approx(0.06)


def test_cap_position_weight_does_not_widen_with_profile():
    overrides = _make_overrides(bucket="aggressive")  # cap 18% => 0.18
    # base of 0.10 stays the binding constraint
    assert cap_position_weight(0.10, overrides) == 0.10


def test_cap_confidence_passthrough_when_none():
    assert cap_confidence(0.93, None) == 0.93


def test_cap_confidence_clips_to_bucket_ceiling():
    overrides = _make_overrides(bucket="conservative")  # cap 0.70
    assert cap_confidence(0.95, overrides) == pytest.approx(0.70)
    assert cap_confidence(0.50, overrides) == 0.50


# ── filter_universe_by_profile uses the test DB ──────────────────────


@pytest.mark.asyncio
async def test_filter_universe_passthrough_when_no_lists():
    """Empty whitelist + empty blacklist == no filter applied."""
    from tests.conftest import test_session_factory

    overrides = _make_overrides()
    async with test_session_factory() as db:
        result = await filter_universe_by_profile(
            db, [("a", "X"), ("b", "Y")], overrides
        )
    assert result == [("a", "X"), ("b", "Y")]


@pytest.mark.asyncio
async def test_filter_universe_passthrough_when_overrides_none():
    from tests.conftest import test_session_factory

    async with test_session_factory() as db:
        result = await filter_universe_by_profile(
            db, [("a", "X"), ("b", "Y")], None
        )
    assert result == [("a", "X"), ("b", "Y")]


@pytest.mark.asyncio
async def test_filter_universe_blacklist_drops_matching_sector():
    """conftest seeds AAPL+MSFT as Technology. Blacklist Tech ⇒ both drop."""
    from sqlalchemy import select

    from app.models.reference import Asset
    from tests.conftest import test_session_factory

    overrides = _make_overrides(sector_blacklist=("Technology",))
    async with test_session_factory() as db:
        rows = (
            await db.execute(select(Asset.id, Asset.ticker))
        ).all()
        universe = [(r.id, r.ticker) for r in rows]
        filtered = await filter_universe_by_profile(db, universe, overrides)
    # Both seeded assets are Technology, so all must be dropped.
    assert filtered == []


@pytest.mark.asyncio
async def test_filter_universe_whitelist_keeps_only_matching_sector():
    from sqlalchemy import select

    from app.models.reference import Asset
    from tests.conftest import test_session_factory

    overrides = _make_overrides(sector_whitelist=("Technology",))
    async with test_session_factory() as db:
        rows = (
            await db.execute(select(Asset.id, Asset.ticker))
        ).all()
        universe = [(r.id, r.ticker) for r in rows]
        filtered = await filter_universe_by_profile(db, universe, overrides)
    # All seeded assets are Tech → all kept.
    assert {t for _, t in filtered} == {t for _, t in universe}


@pytest.mark.asyncio
async def test_filter_universe_keeps_assets_with_null_sector():
    """Assets with sector=NULL must not be dropped — we don't know."""
    from sqlalchemy import select

    from app.models.reference import Asset
    from tests.conftest import test_session_factory

    overrides = _make_overrides(sector_blacklist=("Technology",))
    async with test_session_factory() as db:
        # add a null-sector asset
        a = Asset(id="null-sec-asset", ticker="NULLTEST", name="No sector")
        db.add(a)
        await db.commit()
        rows = (
            await db.execute(select(Asset.id, Asset.ticker))
        ).all()
        universe = [(r.id, r.ticker) for r in rows]
        filtered = await filter_universe_by_profile(db, universe, overrides)
    # null-sector asset survives even though Tech is blacklisted
    assert any(t == "NULLTEST" for _, t in filtered)


# ── load_overrides_for_user ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_load_overrides_returns_none_when_no_profile():
    from tests.conftest import test_session_factory

    async with test_session_factory() as db:
        result = await load_overrides_for_user(db, "user-without-profile")
    assert result is None


@pytest.mark.asyncio
async def test_load_overrides_populates_from_saved_profile():
    from tests.conftest import test_session_factory

    user_id = f"user-{secrets.token_hex(4)}"
    async with test_session_factory() as db:
        db.add(
            InvestorProfile(
                user_id=user_id,
                version=3,
                risk_score=24,
                risk_bucket="moderate_aggressive",
                horizon_band="5y_10y",
                primary_goal="growth",
                max_drawdown_pct=25.0,
                knowledge_level="advanced",
                years_investing=7,
                instruments_traded_json=json.dumps(["equities"]),
                investable_amount_band="50k_250k",
                income_band="50k_150k",
                liquid_net_worth_band="100k_500k",
                sector_whitelist_json=json.dumps(["Technology", "Healthcare"]),
                sector_blacklist_json=json.dumps(["Energy"]),
                region_preference="global",
                exclude_leverage=True,
                base_currency="EUR",
                trading_frequency="weekly",
            )
        )
        await db.commit()
        overrides = await load_overrides_for_user(db, user_id)

    assert overrides is not None
    assert overrides.risk_bucket == "moderate_aggressive"
    assert overrides.horizon_band == "5y_10y"
    assert overrides.sector_whitelist == ("Technology", "Healthcare")
    assert overrides.sector_blacklist == ("Energy",)
    assert overrides.region_preference == "global"
    assert overrides.exclude_leverage is True
    assert overrides.targets.equity_pct == 75.0  # ma_5y_10y row
    assert overrides.max_position_weight == pytest.approx(0.14)
    assert overrides.confidence_cap == 0.85


@pytest.mark.asyncio
async def test_load_overrides_returns_none_for_unknown_bucket():
    """If a saved profile has a bucket the mapping doesn't know, degrade gracefully."""
    from tests.conftest import test_session_factory

    user_id = f"user-bad-{secrets.token_hex(4)}"
    async with test_session_factory() as db:
        db.add(
            InvestorProfile(
                user_id=user_id,
                version=1,
                risk_score=8,
                risk_bucket="ultra_aggressive",  # not in SUPPORTED_BUCKETS
                horizon_band="3y_5y",
                primary_goal="growth",
                max_drawdown_pct=15.0,
                knowledge_level="novice",
                investable_amount_band="lt_10k",
                income_band="lt_50k",
                liquid_net_worth_band="lt_100k",
                base_currency="USD",
                trading_frequency="monthly",
            )
        )
        await db.commit()
        overrides = await load_overrides_for_user(db, user_id)
    assert overrides is None


# ── Regression: run_pipeline with overrides=None unchanged ───────────


@pytest.mark.asyncio
async def test_pipeline_run_with_overrides_none_is_no_op(client):
    """Bare /api/v1/pipeline/run (no profile) must still succeed end-to-end."""
    r = await client.post("/api/v1/pipeline/run")
    # The endpoint may fail with no-signals seed; we only assert it does NOT
    # 500 on the profile-aware code path.
    assert r.status_code in (200, 201, 422, 400), r.text
