"""Paper portfolio endpoints with provenance.

GET  /api/v1/paper/current                                — active paper portfolio
GET  /api/v1/paper                                         — list all
GET  /api/v1/paper/{id}                                    — detail
POST /api/v1/paper/from-recommendation/{recommendation_id} — create from rec
POST /api/v1/paper/{id}/rebalance/{recommendation_id}      — rebalance
GET  /api/v1/paper/{id}/drift                              — compute drift
GET  /api/v1/paper/{id}/events                             — event log
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.schemas.paper import (
    PaperPortfolioDetail, PaperHolding, PaperEvent,
    PaperDriftResponse, PaperCreateRequest,
)
from app.models.validation import PaperPortfolio
from app.models.reference import Asset
from app.services.paper import PaperPortfolioService

router = APIRouter()


def _build_detail(pp: PaperPortfolio, asset_map: dict) -> PaperPortfolioDetail:
    """Build response detail with provenance classification."""
    source_type = getattr(pp, "source_type", None) or "unknown"
    is_demo = source_type not in ("recommendation_paper",)
    lineage_available = bool(getattr(pp, "source_recommendation_id", None))

    holdings_data = pp.current_holdings or {}
    holdings = []
    total_invested = 0.0
    for aid, info in holdings_data.items():
        asset = asset_map.get(aid)
        tw = info.get("target_weight", 0)
        cw = info.get("current_weight", tw)
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

    events = []
    for ev in (getattr(pp, "events_log", None) or []):
        events.append(PaperEvent(
            timestamp=ev.get("timestamp", ""),
            event_type=ev.get("event_type", "unknown"),
            description=ev.get("message", ""),
        ))
    if not events and pp.last_rebalance_at:
        events.append(PaperEvent(timestamp=pp.created_at, event_type="creation", description="Portfolio created"))

    warnings = []
    if is_demo:
        warnings.append("This paper portfolio has no recommendation lineage and should be treated as seed/demo or unverified.")
    drifted = [h for h in holdings if abs(h.drift) > 0.01]
    if drifted:
        warnings.append(f"{len(drifted)} position(s) drifted > 1%")

    return PaperPortfolioDetail(
        id=pp.id, name=pp.name, is_active=pp.is_active,
        source_type=source_type, is_demo=is_demo,
        lineage_available=lineage_available,
        source_recommendation_id=getattr(pp, "source_recommendation_id", None),
        portfolio_value=getattr(pp, "portfolio_value", 100000.0) or 100000.0,
        cash_weight=pp.cash_weight,
        invested_weight=round(total_invested, 4),
        total_rebalances=pp.total_rebalances,
        last_rebalance_at=pp.last_rebalance_at,
        holdings=holdings, events=events, warnings=warnings,
        created_at=pp.created_at,
    )


@router.get("/paper/current", response_model=ApiResponse[PaperPortfolioDetail | None])
async def get_current_paper(db: AsyncSession = Depends(get_db)):
    svc = PaperPortfolioService(db)
    pp = await svc.get_current()
    if not pp:
        return ApiResponse(meta=make_meta(warnings=["No active paper portfolio"]), data=None)
    assets = {a.id: a for a in (await db.execute(select(Asset))).scalars().all()}
    return ApiResponse(meta=make_meta(), data=_build_detail(pp, assets))


@router.get("/paper", response_model=ApiResponse[list[PaperPortfolioDetail]])
async def list_papers(db: AsyncSession = Depends(get_db)):
    svc = PaperPortfolioService(db)
    portfolios = await svc.get_portfolios()
    assets = {a.id: a for a in (await db.execute(select(Asset))).scalars().all()}
    return ApiResponse(meta=make_meta(), data=[_build_detail(p, assets) for p in portfolios])


@router.get("/paper/{portfolio_id}", response_model=ApiResponse[PaperPortfolioDetail])
async def get_paper(portfolio_id: str, db: AsyncSession = Depends(get_db)):
    svc = PaperPortfolioService(db)
    pp = await svc.get_portfolio(portfolio_id)
    if not pp:
        raise HTTPException(status_code=404, detail="Paper portfolio not found")
    assets = {a.id: a for a in (await db.execute(select(Asset))).scalars().all()}
    return ApiResponse(meta=make_meta(), data=_build_detail(pp, assets))


@router.post("/paper/from-recommendation/{recommendation_id}", response_model=ApiResponse[PaperPortfolioDetail])
async def create_from_recommendation(
    recommendation_id: str,
    body: PaperCreateRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    svc = PaperPortfolioService(db)
    starting = body.starting_value if body else 100000.0
    allow = body.allow_unpublished if body else False
    try:
        pp = await svc.create_from_recommendation(recommendation_id, starting, allow)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    assets = {a.id: a for a in (await db.execute(select(Asset))).scalars().all()}
    return ApiResponse(meta=make_meta(), data=_build_detail(pp, assets))


@router.post("/paper/{portfolio_id}/rebalance/{recommendation_id}", response_model=ApiResponse[PaperPortfolioDetail])
async def rebalance_paper(portfolio_id: str, recommendation_id: str, db: AsyncSession = Depends(get_db)):
    svc = PaperPortfolioService(db)
    try:
        pp = await svc.rebalance_from_recommendation(portfolio_id, recommendation_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    assets = {a.id: a for a in (await db.execute(select(Asset))).scalars().all()}
    return ApiResponse(meta=make_meta(), data=_build_detail(pp, assets))


@router.get("/paper/{portfolio_id}/drift", response_model=ApiResponse[PaperDriftResponse])
async def get_drift(portfolio_id: str, db: AsyncSession = Depends(get_db)):
    svc = PaperPortfolioService(db)
    try:
        drift = await svc.compute_drift(portfolio_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ApiResponse(meta=make_meta(), data=PaperDriftResponse(**drift))


@router.get("/paper/{portfolio_id}/events", response_model=ApiResponse[list[PaperEvent]])
async def get_events(portfolio_id: str, db: AsyncSession = Depends(get_db)):
    svc = PaperPortfolioService(db)
    pp = await svc.get_portfolio(portfolio_id)
    if not pp:
        raise HTTPException(status_code=404, detail="Paper portfolio not found")
    events = [
        PaperEvent(timestamp=ev.get("timestamp", ""), event_type=ev.get("event_type", ""), description=ev.get("message", ""))
        for ev in (pp.events_log or [])
    ]
    return ApiResponse(meta=make_meta(), data=events)
