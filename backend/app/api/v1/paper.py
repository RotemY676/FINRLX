"""Paper portfolio endpoints.

GET /api/v1/paper/current — active paper portfolio
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.schemas.paper import PaperPortfolioDetail, PaperHolding, PaperEvent
from app.models.validation import PaperPortfolio
from app.models.reference import Asset

router = APIRouter()


@router.get("/paper/current", response_model=ApiResponse[PaperPortfolioDetail | None])
async def get_current_paper(db: AsyncSession = Depends(get_db)):
    pp = (await db.execute(
        select(PaperPortfolio)
        .where(PaperPortfolio.is_active == True)
        .order_by(PaperPortfolio.created_at.desc())
        .limit(1)
    )).scalar_one_or_none()

    if not pp:
        return ApiResponse(meta=make_meta(warnings=["No active paper portfolio"]), data=None)

    # Build asset lookup
    assets = (await db.execute(select(Asset))).scalars().all()
    asset_map = {a.id: a for a in assets}

    holdings_data = pp.current_holdings or {}
    holdings = []
    total_invested = 0.0
    for aid, info in holdings_data.items():
        asset = asset_map.get(aid)
        tw = info.get("target_weight", 0)
        cw = info.get("current_weight", 0)
        holdings.append(PaperHolding(
            asset_id=aid,
            ticker=info.get("ticker", asset.ticker if asset else "???"),
            name=asset.name if asset else "Unknown",
            target_weight=tw,
            current_weight=cw,
            drift=round(cw - tw, 4),
        ))
        total_invested += cw

    holdings.sort(key=lambda h: h.current_weight, reverse=True)

    # Events from paper_events if stored, otherwise construct from metadata
    events = []
    # PaperPortfolio doesn't have an events column, so we construct from seed conventions
    if pp.last_rebalance_at:
        events.append(PaperEvent(
            timestamp=pp.created_at,
            event_type="creation",
            description="Paper portfolio created from published recommendation.",
        ))
        events.append(PaperEvent(
            timestamp=pp.last_rebalance_at,
            event_type="rebalance",
            description=f"Rebalance #{pp.total_rebalances}: {len(holdings)} positions, {pp.cash_weight*100:.0f}% cash.",
        ))

    # Check for drift warnings
    warnings = []
    drifted = [h for h in holdings if abs(h.drift) > 0.01]
    if drifted:
        warnings.append(
            f"{len(drifted)} position(s) drifted more than 1% from target: "
            + ", ".join(f"{h.ticker} ({h.drift*100:+.1f}%)" for h in drifted[:3])
        )

    return ApiResponse(
        meta=make_meta(),
        data=PaperPortfolioDetail(
            id=pp.id,
            name=pp.name,
            is_active=pp.is_active,
            cash_weight=pp.cash_weight,
            invested_weight=round(total_invested, 4),
            total_rebalances=pp.total_rebalances,
            last_rebalance_at=pp.last_rebalance_at,
            holdings=holdings,
            events=events,
            warnings=warnings,
            created_at=pp.created_at,
        ),
    )
