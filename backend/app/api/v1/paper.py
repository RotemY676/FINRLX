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

from app.api.deps import make_meta
from app.core.database import get_db
from app.models.reference import Asset
from app.models.validation import PaperPortfolio
from app.schemas.common import ApiResponse
from app.schemas.paper import (
    PaperAssetAttribution,
    PaperCreateRequest,
    PaperDecisionAttribution,
    PaperDriftResponse,
    PaperEvent,
    PaperHolding,
    PaperPerformanceSummary,
    PaperPortfolioDetail,
    PaperTradeResponse,
    PaperValuationPoint,
)
from app.services.paper import PaperPortfolioService
from app.services.paper_currency import value_portfolio_in_currency

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
    if source_type in ("seed_demo", "unknown") and not lineage_available:
        warnings.append("This paper portfolio has no recommendation lineage and should be treated as seed/demo or unverified.")
    elif source_type == "test_paper":
        warnings.append("This paper portfolio was created from an unpublished recommendation using allow_unpublished=true and should be treated as test-only.")
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


@router.get(
    "/paper/current/valuation-in-currency",
    response_model=ApiResponse[dict],
)
async def get_current_paper_valuation_in_currency(
    currency: str,
    db: AsyncSession = Depends(get_db),
):
    """Phase FX-2 — translate the active paper portfolio into a currency.

    Query: ``currency=EUR`` (or any 3-letter ISO code supported by
    the FX layer). Returns per-holding native + target valuations,
    aggregate total, and any FX fallback warnings so the UI can show
    a "stale" badge.
    """
    svc = PaperPortfolioService(db)
    pp = await svc.get_current()
    if not pp:
        raise HTTPException(status_code=404, detail="no_active_paper_portfolio")

    if not currency or len(currency) != 3:
        raise HTTPException(
            status_code=422, detail="currency must be a 3-letter ISO code"
        )
    target = currency.upper()

    valuation = await value_portfolio_in_currency(db, pp, target)
    return ApiResponse(
        meta=make_meta(warnings=valuation.fx_warnings),
        data={
            "portfolio_id": valuation.portfolio_id,
            "base_currency": valuation.base_currency,
            "target_currency": valuation.target_currency,
            "as_of_date": valuation.as_of_date.isoformat(),
            "total_value_in_target": valuation.total_value_in_target,
            "holdings": [
                {
                    "asset_id": h.asset_id,
                    "ticker": h.ticker,
                    "asset_currency": h.asset_currency,
                    "quantity": h.quantity,
                    "last_price": h.last_price,
                    "value_native": h.value_native,
                    "value_in_target": h.value_in_base,
                    "fx_rate": h.fx_rate,
                    "fx_rate_date": h.fx_rate_date.isoformat(),
                    "fx_is_fallback": h.fx_is_fallback,
                }
                for h in valuation.holdings
            ],
        },
    )


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


@router.post("/paper/{portfolio_id}/performance/recompute", response_model=ApiResponse[PaperPerformanceSummary])
async def recompute_performance(portfolio_id: str, db: AsyncSession = Depends(get_db)):
    svc = PaperPortfolioService(db)
    await svc.generate_valuation_snapshots(portfolio_id)
    summary = await svc.get_performance_summary(portfolio_id)
    return ApiResponse(meta=make_meta(), data=PaperPerformanceSummary(**summary))


@router.get("/paper/{portfolio_id}/performance", response_model=ApiResponse[PaperPerformanceSummary])
async def get_performance(portfolio_id: str, db: AsyncSession = Depends(get_db)):
    svc = PaperPortfolioService(db)
    summary = await svc.get_performance_summary(portfolio_id)
    return ApiResponse(meta=make_meta(), data=PaperPerformanceSummary(**summary))


@router.get("/paper/{portfolio_id}/valuations", response_model=ApiResponse[list[PaperValuationPoint]])
async def get_valuations(portfolio_id: str, db: AsyncSession = Depends(get_db)):
    svc = PaperPortfolioService(db)
    snaps = await svc.get_valuation_snapshots(portfolio_id)
    return ApiResponse(meta=make_meta(), data=[
        PaperValuationPoint(
            date=s.valuation_date.isoformat()[:10] if s.valuation_date else "",
            portfolio_value=s.portfolio_value,
            daily_return=s.daily_return,
            cumulative_return=s.cumulative_return,
            max_drawdown_to_date=s.max_drawdown_to_date,
        ) for s in snaps
    ])


@router.get("/paper/{portfolio_id}/trades", response_model=ApiResponse[list[PaperTradeResponse]])
async def get_trades(portfolio_id: str, db: AsyncSession = Depends(get_db)):
    svc = PaperPortfolioService(db)
    trades = await svc.get_trades(portfolio_id)
    return ApiResponse(meta=make_meta(), data=[
        PaperTradeResponse(
            id=t.id, trade_date=t.trade_date.isoformat() if t.trade_date else "",
            ticker=t.ticker, side=t.side, quantity=t.quantity,
            price=t.price, notional=t.notional,
            weight_delta=t.weight_delta, reason=t.reason,
        ) for t in trades
    ])


@router.get("/paper/{portfolio_id}/attribution/assets", response_model=ApiResponse[list[PaperAssetAttribution]])
async def get_asset_attribution(portfolio_id: str, db: AsyncSession = Depends(get_db)):
    svc = PaperPortfolioService(db)
    attrib = await svc.get_asset_attribution(portfolio_id)
    return ApiResponse(meta=make_meta(), data=[PaperAssetAttribution(**a) for a in attrib])


@router.get("/paper/{portfolio_id}/attribution/decisions", response_model=ApiResponse[list[PaperDecisionAttribution]])
async def get_decision_attribution(portfolio_id: str, db: AsyncSession = Depends(get_db)):
    svc = PaperPortfolioService(db)
    attrib = await svc.get_decision_attribution(portfolio_id)
    return ApiResponse(meta=make_meta(), data=[PaperDecisionAttribution(**a) for a in attrib])
