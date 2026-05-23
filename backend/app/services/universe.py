"""Universe management service.

Phase 6F: read-only universe inspection with coverage/readiness data.
Phase 20: + CRUD operations (create / rename / deactivate). Deactivation
is "soft" — the row stays for replay of past recommendations, just flagged
is_active=false so it falls out of the live picker. Hard deletes would
strand UniverseMembership and Recommendation foreign keys.
"""
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import gen_uuid
from app.models.feature import FeatureSet, FeatureValue
from app.models.ingestion import MarketBar
from app.models.modeling import ModelPrediction
from app.models.reference import Asset, Universe, UniverseMembership
from app.models.signal import SignalOutput


class UniverseConflictError(Exception):
    """Raised when a CRUD action would violate a business rule (duplicate
    name, deactivating the last active universe, …). The endpoint layer
    translates this into a 409 Conflict."""


class UniverseNotFoundError(Exception):
    """Raised when a CRUD action targets a non-existent universe id. The
    endpoint layer translates this into a 404."""


class UniverseService:

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Phase 20 CRUD ────────────────────────────────────────────────────

    async def create_universe(self, name: str, description: str | None) -> dict:
        """Create a new universe. Raises UniverseConflictError on duplicate
        name (which already maps to a 409 in the endpoint layer)."""
        u = Universe(id=gen_uuid(), name=name, description=description, is_active=True)
        self.db.add(u)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise UniverseConflictError(f"Universe name '{name}' already exists.")
        await self.db.refresh(u)
        detail = await self.get_universe_detail(u.id)
        assert detail is not None
        return detail

    async def update_universe(
        self,
        universe_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
    ) -> dict:
        """PATCH semantics — only the keys explicitly passed are touched.

        Guardrails:
          - rename to a name owned by a different universe → 409
          - deactivating the only currently-active universe → 409
            (the picker would be empty and decision/backtest would 500)
        """
        u = (await self.db.execute(
            select(Universe).where(Universe.id == universe_id)
        )).scalar_one_or_none()
        if u is None:
            raise UniverseNotFoundError(universe_id)

        if name is not None and name != u.name:
            clash = (await self.db.execute(
                select(Universe.id).where(Universe.name == name)
            )).scalar_one_or_none()
            if clash is not None and clash != universe_id:
                raise UniverseConflictError(
                    f"Universe name '{name}' already exists."
                )
            u.name = name
        if description is not None:
            u.description = description
        if is_active is not None and is_active != u.is_active:
            if not is_active:
                # Refuse to deactivate the last active universe — leaves the
                # rest of the product (decision, backtests) without a target.
                active_count = (await self.db.execute(
                    select(func.count())
                    .select_from(Universe)
                    .where(Universe.is_active.is_(True))
                )).scalar() or 0
                if active_count <= 1:
                    raise UniverseConflictError(
                        "Cannot deactivate the only active universe."
                    )
            u.is_active = is_active

        await self.db.commit()
        await self.db.refresh(u)
        detail = await self.get_universe_detail(u.id)
        assert detail is not None
        return detail

    async def deactivate_universe(self, universe_id: str) -> dict:
        """Convenience wrapper for the DELETE endpoint — same guardrails
        as update_universe(is_active=False)."""
        return await self.update_universe(universe_id, is_active=False)

    # ── Existing read-only methods ───────────────────────────────────────

    async def get_universes(self) -> list[dict]:
        universes = (await self.db.execute(
            select(Universe).where(Universe.is_active.is_(True)).order_by(Universe.name)
        )).scalars().all()
        results = []
        for u in universes:
            count = (await self.db.execute(
                select(func.count()).select_from(UniverseMembership)
                .where(UniverseMembership.universe_id == u.id)
            )).scalar() or 0
            results.append({
                "universe_id": u.id,
                "name": u.name,
                "description": u.description,
                "asset_count": count,
            })
        return results

    async def get_default_universe(self) -> dict | None:
        # Phase 20.1 — pick the oldest still-active universe so the "default"
        # is deterministic. Previously this was `LIMIT 1` with no ORDER BY,
        # which worked by accident when there was only one universe.
        u = (await self.db.execute(
            select(Universe)
            .where(Universe.is_active.is_(True))
            .order_by(Universe.created_at.asc())
            .limit(1)
        )).scalar_one_or_none()
        if not u:
            return None
        return await self.get_universe_detail(u.id)

    async def get_universe_detail(self, universe_id: str) -> dict | None:
        u = (await self.db.execute(
            select(Universe).where(Universe.id == universe_id)
        )).scalar_one_or_none()
        if not u:
            return None

        members = (await self.db.execute(
            select(Asset.id, Asset.ticker, Asset.name, Asset.sector, Asset.is_active)
            .join(UniverseMembership, UniverseMembership.asset_id == Asset.id)
            .where(UniverseMembership.universe_id == universe_id)
        )).all()

        tickers = [m.ticker for m in members]
        active = sum(1 for m in members if m.is_active)

        return {
            "universe_id": u.id,
            "name": u.name,
            "description": u.description,
            "asset_count": len(members),
            "active_asset_count": active,
            "tickers": tickers,
            "assets": [{"asset_id": m.id, "ticker": m.ticker, "name": m.name,
                         "sector": m.sector, "is_active": m.is_active} for m in members],
        }

    async def get_asset_coverage(self, universe_id: str) -> dict:
        members = (await self.db.execute(
            select(Asset.id, Asset.ticker)
            .join(UniverseMembership, UniverseMembership.asset_id == Asset.id)
            .where(UniverseMembership.universe_id == universe_id)
        )).all()
        asset_ids = [m.id for m in members]
        total = len(asset_ids)
        if total == 0:
            return {"universe_id": universe_id, "asset_count": 0, "coverage": {}}

        # Market bars coverage
        bar_assets = (await self.db.execute(
            select(func.count(func.distinct(MarketBar.asset_id)))
            .where(MarketBar.asset_id.in_(asset_ids))
        )).scalar() or 0

        # Feature coverage (latest feature set)
        latest_fs = (await self.db.execute(
            select(FeatureSet).order_by(FeatureSet.as_of.desc()).limit(1)
        )).scalar_one_or_none()
        feat_assets = 0
        if latest_fs:
            feat_assets = (await self.db.execute(
                select(func.count(func.distinct(FeatureValue.asset_id)))
                .where(FeatureValue.feature_set_id == latest_fs.id)
                .where(FeatureValue.asset_id.in_(asset_ids))
            )).scalar() or 0

        # Signal coverage (any completed run)
        sig_assets = (await self.db.execute(
            select(func.count(func.distinct(SignalOutput.asset_id)))
            .where(SignalOutput.asset_id.in_(asset_ids))
        )).scalar() or 0

        # Model prediction coverage
        pred_assets = (await self.db.execute(
            select(func.count(func.distinct(ModelPrediction.asset_id)))
            .where(ModelPrediction.asset_id.in_(asset_ids))
        )).scalar() or 0

        return {
            "universe_id": universe_id,
            "asset_count": total,
            "coverage": {
                "market_bars": {"covered": bar_assets, "total": total, "pct": round(bar_assets / total, 2)},
                "features": {"covered": feat_assets, "total": total, "pct": round(feat_assets / total, 2)},
                "signals": {"covered": sig_assets, "total": total, "pct": round(sig_assets / total, 2)},
                "model_predictions": {"covered": pred_assets, "total": total, "pct": round(pred_assets / total, 2)},
            },
        }

    async def get_universe_readiness(self, universe_id: str) -> dict:
        coverage = await self.get_asset_coverage(universe_id)
        cov = coverage.get("coverage", {})
        warnings = []

        bars_pct = cov.get("market_bars", {}).get("pct", 0)
        feat_pct = cov.get("features", {}).get("pct", 0)
        sig_pct = cov.get("signals", {}).get("pct", 0)

        if bars_pct < 1.0:
            warnings.append(f"Market bars cover {bars_pct:.0%} of universe")
        if feat_pct < 1.0:
            warnings.append(f"Features cover {feat_pct:.0%} of universe")
        if sig_pct < 0.5:
            warnings.append(f"Signals cover only {sig_pct:.0%} of universe")

        ready = bars_pct >= 0.8 and feat_pct >= 0.5
        return {
            **coverage,
            "readiness_status": "ready" if ready else "incomplete",
            "warnings": warnings,
        }

    async def get_ops_summary(self) -> dict:
        total_universes = (await self.db.execute(
            select(func.count()).select_from(Universe)
        )).scalar() or 0
        total_assets = (await self.db.execute(
            select(func.count()).select_from(Asset)
        )).scalar() or 0
        default = await self.get_default_universe()
        default_readiness = None
        if default:
            r = await self.get_universe_readiness(default["universe_id"])
            default_readiness = r.get("readiness_status")
        return {
            "total_universes": total_universes,
            "total_assets": total_assets,
            "default_universe_name": default["name"] if default else None,
            "default_readiness": default_readiness,
        }
