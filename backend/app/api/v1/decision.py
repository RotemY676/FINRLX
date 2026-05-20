"""Decision pipeline stage endpoints.

GET /api/v1/recommendations/{id}/stages — all pipeline stages for a recommendation.
Maps to API Contract doc 12, Decision Breakdown.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import make_meta
from app.core.database import get_db
from app.models.decision_pipeline import (
    AllocationResult,
    RiskOverlayResult,
    SelectionRun,
    TimingResult,
)
from app.models.reference import Asset
from app.schemas.common import ApiResponse
from app.schemas.decision import (
    AllocationEntry,
    AllocationView,
    AssetSelection,
    DecisionStagesResponse,
    RiskAdjustment,
    RiskOverlayView,
    SelectionRunView,
    TimingView,
)

router = APIRouter()


@router.get(
    "/recommendations/{recommendation_id}/stages",
    response_model=ApiResponse[DecisionStagesResponse],
)
async def get_decision_stages(recommendation_id: str, db: AsyncSession = Depends(get_db)):
    """Return all decision pipeline stages for a recommendation."""
    # Build asset lookup
    assets_result = await db.execute(select(Asset))
    asset_map = {a.id: a for a in assets_result.scalars().all()}

    def ticker_for(aid: str) -> str:
        return asset_map[aid].ticker if aid in asset_map else "???"

    # Selection
    sel_result = await db.execute(
        select(SelectionRun).where(SelectionRun.recommendation_id == recommendation_id)
    )
    sel = sel_result.scalar_one_or_none()
    selection = None
    if sel:
        included = sel.included_assets or []
        excluded = sel.excluded_assets or []
        selection = SelectionRunView(
            id=sel.id,
            recommendation_id=recommendation_id,
            included=[AssetSelection(
                asset_id=i.get("asset_id", ""),
                ticker=i.get("ticker", ticker_for(i.get("asset_id", ""))),
                reason=i.get("reason"),
            ) for i in included],
            excluded=[AssetSelection(
                asset_id=e.get("asset_id", ""),
                ticker=e.get("ticker", ticker_for(e.get("asset_id", ""))),
                reason=e.get("reason"),
            ) for e in excluded],
            rationale=sel.rationale,
            created_at=sel.created_at,
        )

    # Allocation
    alloc_result = await db.execute(
        select(AllocationResult).where(AllocationResult.recommendation_id == recommendation_id)
    )
    alloc = alloc_result.scalar_one_or_none()
    allocation = None
    if alloc:
        weights_dict = alloc.weights or {}
        allocation = AllocationView(
            id=alloc.id,
            recommendation_id=recommendation_id,
            method=alloc.method,
            entries=[AllocationEntry(
                asset_id=aid,
                ticker=ticker_for(aid),
                weight=w,
            ) for aid, w in weights_dict.items()],
            rationale=alloc.rationale,
            created_at=alloc.created_at,
        )

    # Timing
    timing_result = await db.execute(
        select(TimingResult).where(TimingResult.recommendation_id == recommendation_id)
    )
    timing_row = timing_result.scalar_one_or_none()
    timing = None
    if timing_row:
        timing = TimingView(
            id=timing_row.id,
            recommendation_id=recommendation_id,
            urgency=timing_row.urgency,
            horizon_days=timing_row.horizon_days,
            rationale=timing_row.rationale,
            created_at=timing_row.created_at,
        )

    # Risk overlay
    risk_result = await db.execute(
        select(RiskOverlayResult).where(RiskOverlayResult.recommendation_id == recommendation_id)
    )
    risk_row = risk_result.scalar_one_or_none()
    risk_overlay = None
    if risk_row:
        adjustments = risk_row.adjustments or []
        risk_overlay = RiskOverlayView(
            id=risk_row.id,
            recommendation_id=recommendation_id,
            portfolio_risk_score=risk_row.portfolio_risk_score,
            adjustments=[RiskAdjustment(
                asset_id=a.get("asset_id", ""),
                ticker=a.get("ticker", ticker_for(a.get("asset_id", ""))),
                pre_weight=a.get("pre_weight", 0),
                post_weight=a.get("post_weight", 0),
                delta=a.get("delta", 0),
                reason=a.get("reason"),
            ) for a in adjustments],
            constraints_applied=risk_row.constraints_applied or [],
            rationale=risk_row.rationale,
            created_at=risk_row.created_at,
        )

    return ApiResponse(
        meta=make_meta(),
        data=DecisionStagesResponse(
            recommendation_id=recommendation_id,
            selection=selection,
            allocation=allocation,
            timing=timing,
            risk_overlay=risk_overlay,
        ),
    )
