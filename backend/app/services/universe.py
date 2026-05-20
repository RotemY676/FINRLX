"""Universe management service.

Phase 6F: read-only universe inspection with coverage/readiness data.
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feature import FeatureSet, FeatureValue
from app.models.ingestion import MarketBar
from app.models.modeling import ModelPrediction
from app.models.reference import Asset, Universe, UniverseMembership
from app.models.signal import SignalOutput


class UniverseService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_universes(self) -> list[dict]:
        universes = (await self.db.execute(
            select(Universe).order_by(Universe.name)
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
        u = (await self.db.execute(select(Universe).limit(1))).scalar_one_or_none()
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
