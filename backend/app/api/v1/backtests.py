"""Backtest endpoints.

GET /api/v1/backtests — list experiments
GET /api/v1/backtests/{id} — experiment detail
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.schemas.backtest import (
    BacktestDetail, BacktestListItem, BacktestListResponse,
    BacktestResultSummary, EquityCurvePoint,
)
from app.models.validation import BacktestExperiment
from app.models.reference import Universe

router = APIRouter()


@router.get("/backtests", response_model=ApiResponse[BacktestListResponse])
async def list_backtests(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(BacktestExperiment).order_by(BacktestExperiment.created_at.desc())
    )).scalars().all()

    items = []
    for bt in rows:
        rs = bt.results_summary or {}
        items.append(BacktestListItem(
            id=bt.id,
            name=bt.name,
            status=bt.status,
            start_date=bt.start_date,
            end_date=bt.end_date,
            is_promoted=bt.is_promoted,
            total_return=rs.get("total_return"),
            sharpe_ratio=rs.get("sharpe_ratio"),
        ))

    return ApiResponse(
        meta=make_meta(),
        data=BacktestListResponse(items=items, total=len(items)),
    )


@router.get("/backtests/{backtest_id}", response_model=ApiResponse[BacktestDetail])
async def get_backtest(backtest_id: str, db: AsyncSession = Depends(get_db)):
    bt = (await db.execute(
        select(BacktestExperiment).where(BacktestExperiment.id == backtest_id)
    )).scalar_one_or_none()
    if not bt:
        raise HTTPException(status_code=404, detail="Backtest not found")

    rs = bt.results_summary or {}
    universe_name = None
    if bt.universe_id:
        uni = (await db.execute(
            select(Universe).where(Universe.id == bt.universe_id)
        )).scalar_one_or_none()
        if uni:
            universe_name = uni.name

    equity_curve = [
        EquityCurvePoint(date=p["date"], value=p["value"])
        for p in rs.get("equity_curve", [])
    ]

    return ApiResponse(
        meta=make_meta(),
        data=BacktestDetail(
            id=bt.id,
            name=bt.name,
            status=bt.status,
            universe_name=universe_name,
            policy_version_id=bt.policy_version_id,
            start_date=bt.start_date,
            end_date=bt.end_date,
            is_promoted=bt.is_promoted,
            config=bt.config or {},
            results=BacktestResultSummary(
                total_return=rs.get("total_return"),
                annualized_return=rs.get("annualized_return"),
                max_drawdown=rs.get("max_drawdown"),
                sharpe_ratio=rs.get("sharpe_ratio"),
                volatility=rs.get("volatility"),
                total_trades=rs.get("total_trades"),
                avg_turnover=rs.get("avg_turnover"),
            ),
            equity_curve=equity_curve,
            warnings=rs.get("warnings", []),
            created_at=bt.created_at,
        ),
    )
