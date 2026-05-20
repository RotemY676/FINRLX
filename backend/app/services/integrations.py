"""Integrations service.

Phase 6F: makes data/source integrations visible and governable.
Truthfully distinguishes real local adapters from illustrative/placeholder entries.
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingestion import IngestionManifest
from app.models.ops import DataFeed

# Real providers are those backed by actual IngestService adapters
REAL_PROVIDERS = {"local_deterministic", "seed", "local", "yfinance"}

# Known placeholder/demo feed names from seeded data
PLACEHOLDER_FEED_NAMES = {
    "Reuters · news intel", "Bloomberg · price feed", "Options flow · CBOE",
    "Earnings · Factset", "Alt data · satellite",
}


class IntegrationsService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_integrations(self) -> list[dict]:
        """List all integrations, truthfully labeled."""
        feeds = (await self.db.execute(
            select(DataFeed).order_by(DataFeed.name)
        )).scalars().all()

        # Get latest manifest per source
        manifests = (await self.db.execute(
            select(IngestionManifest)
            .order_by(IngestionManifest.completed_at.desc())
        )).scalars().all()
        manifest_by_source: dict[str, IngestionManifest] = {}
        for m in manifests:
            if m.source not in manifest_by_source:
                manifest_by_source[m.source] = m

        results = []

        # Add local adapters from manifests
        for source_key, manifest in manifest_by_source.items():
            is_real = source_key in REAL_PROVIDERS
            warnings_list = []
            if not is_real:
                warnings_list.append(f"Source '{source_key}' is not a verified real provider")
            status = "healthy" if manifest.status == "completed" and is_real else "placeholder" if not is_real else "degraded"
            results.append({
                "source_key": source_key,
                "name": f"Local adapter ({source_key})",
                "category": "market_data" if manifest.kind == "bars" else "news",
                "status": status,
                "is_real_provider": is_real,
                "is_placeholder": not is_real,
                "last_manifest_id": manifest.id,
                "last_success_at": manifest.completed_at.isoformat() if manifest.completed_at else None,
                "freshness": "current" if manifest.status == "completed" else "stale",
                "coverage": f"{manifest.asset_count} assets, {manifest.row_count} rows",
                "warnings": warnings_list,
                "next_action": "connect_real_provider" if not is_real else None,
            })

        # Add illustrative/placeholder feeds from DataFeed table
        for f in feeds:
            is_placeholder = f.name in PLACEHOLDER_FEED_NAMES
            warnings = []
            if is_placeholder:
                warnings.append("Placeholder/demo feed — not backed by real integration")
            results.append({
                "source_key": f.name.lower().replace(" ", "_").replace("·", "").replace("__", "_").strip("_"),
                "name": f.name,
                "category": self._categorize_feed(f.name),
                "status": f.status if not is_placeholder else "placeholder",
                "is_real_provider": not is_placeholder,
                "is_placeholder": is_placeholder,
                "last_manifest_id": None,
                "last_success_at": f.last_checked_at.isoformat() if f.last_checked_at else None,
                "freshness": f.lag or "unknown",
                "coverage": f.coverage or "unknown",
                "warnings": warnings,
                "next_action": "connect_real_provider" if is_placeholder else None,
            })

        return results

    def _categorize_feed(self, name: str) -> str:
        n = name.lower()
        if "price" in n or "bloomberg" in n:
            return "market_data"
        if "news" in n or "reuters" in n or "sentiment" in n:
            return "news"
        if "options" in n or "cboe" in n or "flow" in n:
            return "market_data"
        if "earnings" in n or "factset" in n or "fundamental" in n:
            return "fundamentals"
        if "alt" in n or "satellite" in n:
            return "sentiment"
        if "internal" in n:
            return "market_data"
        return "market_data"

    async def get_integration_detail(self, source_key: str) -> dict | None:
        integrations = await self.get_integrations()
        for i in integrations:
            if i["source_key"] == source_key:
                return i
        return None

    async def get_integration_health(self) -> dict:
        integrations = await self.get_integrations()
        total = len(integrations)
        healthy = sum(1 for i in integrations if i["status"] == "healthy")
        placeholder = sum(1 for i in integrations if i["is_placeholder"])
        real = sum(1 for i in integrations if i["is_real_provider"])
        degraded = sum(1 for i in integrations if i["status"] in ("degraded", "stale"))
        return {
            "total_integrations": total,
            "healthy": healthy,
            "degraded": degraded,
            "placeholder": placeholder,
            "real_providers": real,
            "all_real_healthy": healthy == real and real > 0,
        }

    async def get_provider_readiness(self) -> dict:
        health = await self.get_integration_health()
        manifests = (await self.db.execute(
            select(func.count()).select_from(IngestionManifest)
            .where(IngestionManifest.status == "completed")
        )).scalar() or 0
        return {
            **health,
            "completed_manifests": manifests,
            "ready_for_pipeline": manifests > 0,
        }
