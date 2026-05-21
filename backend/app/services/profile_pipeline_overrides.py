"""Phase W-5 — wire an investor profile into the decision pipeline.

Pure helpers + a single async loader. The decision pipeline accepts an
optional ``ProfileOverrides`` parameter:

* if ``None`` → pipeline behaves exactly as it did before W-5 (no
  behavior change, preserved by tests).
* if set → the universe is filtered by the profile's sector lists, the
  risk overlay uses the profile's ``max_position_pct``, and the final
  model-confidence is clipped to the profile's ``confidence_cap``.

Keeping all profile-aware logic in a separate module means the
pipeline.py diff stays surgical and easy to audit.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import InvestorProfile
from app.models.reference import Asset
from app.services.profile_mapping import (
    AllocationMappingError,
    AllocationTargets,
    derive_allocation,
)


@dataclass(frozen=True)
class ProfileOverrides:
    profile_id: str
    profile_version: int
    risk_bucket: str
    horizon_band: str
    sector_whitelist: tuple[str, ...]
    sector_blacklist: tuple[str, ...]
    region_preference: str
    exclude_leverage: bool
    targets: AllocationTargets

    @property
    def max_position_weight(self) -> float:
        """Per-asset weight cap as a 0-1 ratio."""
        return self.targets.max_position_pct / 100.0

    @property
    def confidence_cap(self) -> float:
        return self.targets.confidence_cap


async def load_overrides_for_user(
    db: AsyncSession, user_id: str
) -> ProfileOverrides | None:
    """Load the user's current profile and translate to overrides.

    Returns ``None`` if the user has no profile or the bucket/horizon
    cannot be mapped (which would only happen if the saved values drift
    out of sync with the supported sets — we degrade gracefully rather
    than failing the pipeline).
    """
    profile = (
        await db.execute(
            select(InvestorProfile).where(InvestorProfile.user_id == user_id)
        )
    ).scalar_one_or_none()
    if profile is None:
        return None

    try:
        targets = derive_allocation(profile.risk_bucket, profile.horizon_band)
    except AllocationMappingError:
        return None

    return ProfileOverrides(
        profile_id=profile.id,
        profile_version=profile.version,
        risk_bucket=profile.risk_bucket,
        horizon_band=profile.horizon_band,
        sector_whitelist=tuple(json.loads(profile.sector_whitelist_json or "[]")),
        sector_blacklist=tuple(json.loads(profile.sector_blacklist_json or "[]")),
        region_preference=profile.region_preference,
        exclude_leverage=profile.exclude_leverage,
        targets=targets,
    )


async def filter_universe_by_profile(
    db: AsyncSession,
    universe_assets: list[tuple[str, str]],
    overrides: ProfileOverrides | None,
) -> list[tuple[str, str]]:
    """Apply the profile's sector lists to a (asset_id, ticker) universe.

    * If a non-empty ``sector_whitelist`` is set, only those sectors pass.
    * If a non-empty ``sector_blacklist`` is set, those sectors are dropped.
    * If both are empty (or overrides is None), the universe is returned
      unchanged.

    Assets with a NULL sector are kept (we don't know what to filter on).
    """
    if overrides is None or (
        not overrides.sector_whitelist and not overrides.sector_blacklist
    ):
        return universe_assets
    if not universe_assets:
        return universe_assets

    asset_ids = [aid for aid, _ in universe_assets]
    rows = (
        await db.execute(
            select(Asset.id, Asset.sector).where(Asset.id.in_(asset_ids))
        )
    ).all()
    sector_by_id: dict[str, str | None] = {r.id: r.sector for r in rows}

    whitelist = set(overrides.sector_whitelist)
    blacklist = set(overrides.sector_blacklist)

    kept: list[tuple[str, str]] = []
    for aid, ticker in universe_assets:
        sector = sector_by_id.get(aid)
        if sector is None:
            kept.append((aid, ticker))
            continue
        if whitelist and sector not in whitelist:
            continue
        if blacklist and sector in blacklist:
            continue
        kept.append((aid, ticker))
    return kept


def cap_position_weight(
    base_cap: float, overrides: ProfileOverrides | None
) -> float:
    """Return the tighter of the pipeline's base cap and the profile cap."""
    if overrides is None:
        return base_cap
    return min(base_cap, overrides.max_position_weight)


def cap_confidence(
    value: float, overrides: ProfileOverrides | None
) -> float:
    """Clip a confidence value to the profile's confidence_cap."""
    if overrides is None:
        return value
    return min(value, overrides.confidence_cap)
