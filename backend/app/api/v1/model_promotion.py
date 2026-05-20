"""ML promotion review endpoints.

POST /api/v1/models/promotion/review
GET  /api/v1/models/promotion/latest
GET  /api/v1/models/promotion/history
GET  /api/v1/models/promotion/{review_id}
POST /api/v1/models/promotion/{review_id}/decision
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import make_meta
from app.core.database import get_db
from app.models.modeling import MLPromotionReview
from app.schemas.common import ApiResponse
from app.services.ml_promotion import MLPromotionService

router = APIRouter()


class PromotionReviewRequest(BaseModel):
    model_key: str = "ml_return_forecaster"
    start_date: str | None = None
    end_date: str | None = None


class PromotionDecisionRequest(BaseModel):
    decision: str = Field(..., description="One of: keep_shadow, request_more_data, eligible_for_review, reject")


def _review_dict(r: MLPromotionReview) -> dict:
    return {
        "id": r.id,
        "model_key": r.model_key,
        "model_version": r.model_version,
        "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
        "baseline_backtest_id": r.baseline_backtest_id,
        "shadow_backtest_id": r.shadow_backtest_id,
        "validation_report_id": r.validation_report_id,
        "baseline_metrics": r.baseline_metrics,
        "shadow_metrics": r.shadow_metrics,
        "metric_deltas": r.metric_deltas,
        "sample_count": r.sample_count,
        "recommendation": r.recommendation,
        "decision": r.decision,
        "warnings": r.warnings,
    }


@router.post("/models/promotion/review", response_model=ApiResponse[dict])
async def run_promotion_review(
    body: PromotionReviewRequest = PromotionReviewRequest(),
    db: AsyncSession = Depends(get_db),
):
    """Run baseline + shadow backtests and produce a promotion review."""
    svc = MLPromotionService(db)
    start = date.fromisoformat(body.start_date) if body.start_date else None
    end = date.fromisoformat(body.end_date) if body.end_date else None
    review = await svc.run_shadow_backtest_review(body.model_key, start, end)
    return ApiResponse(
        meta=make_meta(warnings=review.warnings),
        data=_review_dict(review),
    )


@router.get("/models/promotion/latest", response_model=ApiResponse[dict | None])
async def get_latest_promotion(db: AsyncSession = Depends(get_db)):
    svc = MLPromotionService(db)
    review = await svc.get_latest_promotion_review("ml_return_forecaster")
    if not review:
        return ApiResponse(meta=make_meta(warnings=["No promotion review exists"]), data=None)
    return ApiResponse(meta=make_meta(), data=_review_dict(review))


@router.get("/models/promotion/history", response_model=ApiResponse[list[dict]])
async def get_promotion_history(db: AsyncSession = Depends(get_db)):
    svc = MLPromotionService(db)
    reviews = await svc.get_promotion_review_history("ml_return_forecaster")
    return ApiResponse(meta=make_meta(), data=[_review_dict(r) for r in reviews])


@router.get("/models/promotion/{review_id}", response_model=ApiResponse[dict])
async def get_promotion_review(review_id: str, db: AsyncSession = Depends(get_db)):
    svc = MLPromotionService(db)
    review = await svc.get_review_by_id(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Promotion review not found")
    return ApiResponse(meta=make_meta(), data=_review_dict(review))


@router.post("/models/promotion/{review_id}/decision", response_model=ApiResponse[dict])
async def record_promotion_decision(
    review_id: str, body: PromotionDecisionRequest, db: AsyncSession = Depends(get_db),
):
    """Record an operator decision. Does NOT activate ML in live scoring."""
    svc = MLPromotionService(db)
    try:
        review = await svc.record_decision(review_id, body.decision)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not review:
        raise HTTPException(status_code=404, detail="Promotion review not found")
    return ApiResponse(meta=make_meta(), data=_review_dict(review))
