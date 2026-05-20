"""Backtest endpoints with provenance.

POST /api/v1/backtests/run            — trigger walk-forward backtest
GET  /api/v1/backtests                — list with source_type/is_demo
GET  /api/v1/backtests/status         — counts
GET  /api/v1/backtests/{id}           — detail with provenance
GET  /api/v1/backtests/{id}/equity-curve — equity curve only
GET  /api/v1/backtests/{id}/decisions  — decision points only
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import make_meta
from app.core.database import get_db
from app.models.reference import Universe
from app.models.validation import BacktestExperiment
from app.schemas.backtest import (
    BacktestDecisionPoint,
    BacktestDetail,
    BacktestListItem,
    BacktestListResponse,
    BacktestProvenance,
    BacktestResultSummary,
    BacktestRunRequest,
    BacktestStatusResponse,
    EquityCurvePoint,
)
from app.schemas.common import ApiResponse
from app.services.backtesting import BacktestService

router = APIRouter()


def _classify_backtest(bt: BacktestExperiment) -> tuple[str, bool, bool]:
    """Return (source_type, is_demo, lineage_available) for a backtest."""
    rs = bt.results_summary or {}
    source_type = rs.get("source_type", "unknown")
    if source_type == "pipeline_backtest":
        return "pipeline_backtest", False, bool(rs.get("recommendation_ids"))
    # Legacy seeded backtests have no source_type field
    if source_type == "unknown" and not rs.get("recommendation_ids"):
        return "seed_demo", True, False
    return source_type, source_type != "pipeline_backtest", bool(rs.get("recommendation_ids"))


def _build_detail(bt: BacktestExperiment, universe_name: str | None = None) -> BacktestDetail:
    rs = bt.results_summary or {}
    source_type, is_demo, lineage_available = _classify_backtest(bt)

    equity_curve = [EquityCurvePoint(date=p["date"], value=p["value"]) for p in rs.get("equity_curve", [])]
    decision_points = [BacktestDecisionPoint(**dp) for dp in rs.get("decision_points", [])]
    warnings = list(rs.get("warnings", []))

    if is_demo:
        warnings.insert(0, "This backtest has no pipeline lineage and should be treated as seed/demo or unverified.")

    provenance = None
    if lineage_available:
        provenance = BacktestProvenance(
            recommendation_ids=rs.get("recommendation_ids", []),
            source_feature_set_ids=rs.get("source_feature_set_ids", []),
            source_signal_run_ids=rs.get("source_signal_run_ids", []),
            market_bar_window=rs.get("market_bar_window"),
            rebalance_dates=rs.get("rebalance_dates", []),
            created_by_service=rs.get("created_by_service"),
        )

    return BacktestDetail(
        id=bt.id, name=bt.name, status=bt.status,
        source_type=source_type, is_demo=is_demo, lineage_available=lineage_available,
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
        decision_points=decision_points,
        provenance=provenance,
        warnings=warnings,
        created_at=bt.created_at,
    )


@router.post("/backtests/run", response_model=ApiResponse[BacktestDetail])
async def run_backtest(body: BacktestRunRequest, db: AsyncSession = Depends(get_db)):
    svc = BacktestService(db)
    start = date.fromisoformat(body.start_date) if body.start_date else None
    end = date.fromisoformat(body.end_date) if body.end_date else None
    bt = await svc.run_backtest(
        name=body.name, start_date=start, end_date=end,
        universe_id=body.universe_id, rebalance_frequency=body.rebalance_frequency,
        cost_bps=body.cost_bps,
    )
    detail = _build_detail(bt)
    return ApiResponse(meta=make_meta(warnings=detail.warnings if detail.warnings else None), data=detail)


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
        source_type, is_demo, lineage_available = _classify_backtest(bt)
        items.append(BacktestListItem(
            id=bt.id, name=bt.name, status=bt.status,
            source_type=source_type, is_demo=is_demo,
            lineage_available=lineage_available,
            decision_count=len(rs.get("decision_points", [])),
            warning_count=len(rs.get("warnings", [])),
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

    universe_name = None
    if bt.universe_id:
        uni = (await db.execute(select(Universe).where(Universe.id == bt.universe_id))).scalar_one_or_none()
        if uni:
            universe_name = uni.name

    return ApiResponse(meta=make_meta(), data=_build_detail(bt, universe_name))


@router.get("/backtests/{backtest_id}/equity-curve", response_model=ApiResponse[list[EquityCurvePoint]])
async def get_equity_curve(backtest_id: str, db: AsyncSession = Depends(get_db)):
    bt = (await db.execute(
        select(BacktestExperiment).where(BacktestExperiment.id == backtest_id)
    )).scalar_one_or_none()
    if not bt:
        raise HTTPException(status_code=404, detail="Backtest not found")
    rs = bt.results_summary or {}
    curve = [EquityCurvePoint(date=p["date"], value=p["value"]) for p in rs.get("equity_curve", [])]
    return ApiResponse(meta=make_meta(), data=curve)


@router.get("/backtests/{backtest_id}/decisions", response_model=ApiResponse[list[BacktestDecisionPoint]])
async def get_decisions(backtest_id: str, db: AsyncSession = Depends(get_db)):
    bt = (await db.execute(
        select(BacktestExperiment).where(BacktestExperiment.id == backtest_id)
    )).scalar_one_or_none()
    if not bt:
        raise HTTPException(status_code=404, detail="Backtest not found")
    rs = bt.results_summary or {}
    points = [BacktestDecisionPoint(**dp) for dp in rs.get("decision_points", [])]
    return ApiResponse(meta=make_meta(), data=points)
