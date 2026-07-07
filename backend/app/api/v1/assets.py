"""Asset search endpoint — Phase 20.3.

GET /api/v1/assets?q=AA&limit=20

Powers the ticker-autocomplete on the /universe Add-asset modal. The
endpoint is read-only and queries the `assets` table only — asset
creation happens via ingestion, not the universe UI.

Ranking
-------
Results favour exact-prefix matches first (so typing "AA" surfaces
"AAPL" above "BABA"), then substring matches on the ticker, then
substring on the name. Within each tier we sort alphabetically by
ticker for stable ordering.

Empty `q` returns the first `limit` active assets sorted by ticker —
useful as a "browse all" mode in the picker.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import make_meta
from app.core.database import get_db
from app.models.reference import Asset
from app.schemas.common import ApiResponse

router = APIRouter()


def _asset_dict(a) -> dict:
    return {
        "asset_id": a.id,
        "ticker": a.ticker,
        "name": a.name,
        "sector": a.sector,
        "is_active": a.is_active,
    }


@router.get("/assets", response_model=ApiResponse[list[dict]])
async def search_assets(
    q: str = Query(default="", max_length=64),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    q_norm = q.strip().upper()
    if not q_norm:
        # No query — return the first `limit` active assets, alphabetical.
        rows = (await self_select_active(db, limit)).scalars().all()
        return ApiResponse(meta=make_meta(), data=[_asset_dict(a) for a in rows])

    # 1. Prefix match on ticker — the most likely user intent.
    prefix_rows = (await db.execute(
        select(Asset)
        .where(Asset.is_active.is_(True))
        .where(func.upper(Asset.ticker).like(f"{q_norm}%"))
        .order_by(Asset.ticker)
        .limit(limit)
    )).scalars().all()

    seen = {a.id for a in prefix_rows}
    remaining = limit - len(prefix_rows)
    substring_rows = []
    if remaining > 0:
        # 2. Substring on ticker (excluding what prefix already returned),
        #    then substring on name. UNION-style fallback to fill the budget.
        substring_rows = (await db.execute(
            select(Asset)
            .where(Asset.is_active.is_(True))
            .where(
                or_(
                    func.upper(Asset.ticker).like(f"%{q_norm}%"),
                    func.upper(Asset.name).like(f"%{q_norm}%"),
                )
            )
            .order_by(Asset.ticker)
            .limit(remaining + len(prefix_rows))
        )).scalars().all()
        # Filter out anything already in prefix_rows; preserve order.
        substring_rows = [a for a in substring_rows if a.id not in seen][:remaining]

    combined = list(prefix_rows) + substring_rows
    return ApiResponse(meta=make_meta(), data=[_asset_dict(a) for a in combined])


async def self_select_active(db: AsyncSession, limit: int):
    """Tiny helper kept separate so the empty-q branch reads top-to-bottom."""
    return await db.execute(
        select(Asset)
        .where(Asset.is_active.is_(True))
        .order_by(Asset.ticker)
        .limit(limit)
    )
