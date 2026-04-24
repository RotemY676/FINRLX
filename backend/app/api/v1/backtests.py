"""Backtest endpoints.

POST /api/v1/backtests/run    — trigger a new backtest
GET  /api/v1/backtests        — list experiments
GET  /api/v1/backtests/status — backtest layer status
GET  /api/v1/backtests/{id}   — experiment detail
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.schemas.backtest import (
    BacktestDetail, BacktestListItem, BacktestListResponse,
    BacktestResultSummary, EquityCurvePoint,
    BacktestRunRequest, BacktestStatusResponse,
)
from app.models.validation import BacktestExperiment
from app.models.reference import Universe
from app.services.backtesting import BacktestService

router = APIRouter()


@router.post("/backtests/run", response_model=ApiResponse[BacktestDetail])
async def run_backtest(body: BacktestRunRequest, db: AsyncSession = Depends(get_db)):
    svc = BacktestService(db)

    start = date.fromisoformat(body.start_date) if body.start_date else None
    end = date.fromisoformat(body.end_date) if body.end_date else None

    bt = await svc.run_backtest(
        name=body.name,
        start_date=start,
        end_date=end,
        universe_id=body.universe_id,
        rebalance_frequency=body.rebalance_frequency,
        cost_bps=body.cost_bps,
    )

    rs = bt.results_summary or {}
    equity_curve = [EquityCurvePoint(date=p["date"], value=p["value"]) for p in rs.get("equity_curve", [])]

    return ApiResponse(
        meta=make_meta(warnings=rs.get("warnings")),
        data=BacktestDetail(
            id=bt.id, name=bt.name, status=bt.status,
            start_date=bt.start_date, end_date=bt.end_date,
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


@router.get("/backtests/status", response_model=ApiResponse[BacktestStatusResponse])
async def get_backtest_status(db: AsyncSession = Depends(get_db)):
    svc = BacktestService(db)
    status = await svc.get_backtest_status()
    return ApiResponse(meta=make_meta(), data=BacktestStatusResponse(**status))


@router.get("/backtests", response_model=ApiResponse[BacktestListResponse])
async def list_backtests(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(BacktestExperiment).order_by(BacktestExperiment.created_at.desc())
    )).scalars().all()

    items = []
    for bt in rows:
        rs = bt.results_summary or {}
        items.append(BacktestListItem(
            id=bt.id, name=bt.name, status=bt.status,
            start_date=bt.start_date, end_date=bt.end_date,
            is_promoted=bt.is_promoted,
            total_return=rs.get("total_return"),
            sharpe_ratio=rs.get("sharpe_ratio"),
        ))

    return ApiResponse(meta=make_meta(), data=BacktestListResponse(items=items, total=len(items)))


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
        uni = (await db.execute(select(Universe).where(Universe.id == bt.universe_id))).scalar_one_or_none()
        if uni:
            universe_name = uni.name

    equity_curve = [EquityCurvePoint(date=p["date"], value=p["value"]) for p in rs.get("equity_curve", [])]

    return ApiResponse(
        meta=make_meta(),
        data=BacktestDetail(
            id=bt.id, name=bt.name, status=bt.status,
            universe_name=universe_name,
            policy_version_id=bt.policy_version_id,
            start_date=bt.start_date, end_date=bt.end_date,
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
