"""Phase B1 — risk metrics endpoints.

GET /api/v1/risk/portfolios/{portfolio_id}  — full risk bundle for a given portfolio
GET /api/v1/risk/current                    — risk bundle for the current/active paper portfolio
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import make_meta
from app.core.database import get_db
from app.models.validation import PaperPortfolio
from app.schemas.common import ApiResponse
from app.schemas.risk import RiskBundle
from app.services.risk_metrics import RiskMetricsService

router = APIRouter()


@router.get("/risk/portfolios/{portfolio_id}", response_model=ApiResponse[RiskBundle])
async def get_risk_for_portfolio(portfolio_id: str, db: AsyncSession = Depends(get_db)):
    svc = RiskMetricsService(db)
    bundle = await svc.get_risk_bundle(portfolio_id)
    if bundle is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return ApiResponse(meta=make_meta(), data=RiskBundle.model_validate(bundle))


@router.get("/risk/current", response_model=ApiResponse[RiskBundle | None])
async def get_risk_for_current_portfolio(db: AsyncSession = Depends(get_db)):
    """Risk bundle for the most recently active paper portfolio.

    Returns null when no paper portfolio exists yet.
    """
    pp = (await db.execute(
        select(PaperPortfolio)
        .where(PaperPortfolio.is_active.is_(True))
        .order_by(PaperPortfolio.created_at.desc())
        .limit(1)
    )).scalar_one_or_none()
    if pp is None:
        return ApiResponse(meta=make_meta(), data=None)
    svc = RiskMetricsService(db)
    bundle = await svc.get_risk_bundle(pp.id)
    if bundle is None:
        return ApiResponse(meta=make_meta(), data=None)
    return ApiResponse(meta=make_meta(), data=RiskBundle.model_validate(bundle))
