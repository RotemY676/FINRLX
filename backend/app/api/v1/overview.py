"""Overview endpoint.

GET /api/v1/overview — current recommendation summary + system health.
Maps to API Contract doc 12.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.schemas.overview import OverviewResponse, HealthSummary
from app.schemas.recommendation import RecommendationSummary, ConfidenceTriplet
from app.models.recommendation import Recommendation, RecommendationWeight

router = APIRouter()


@router.get("/overview", response_model=ApiResponse[OverviewResponse])
async def get_overview(db: AsyncSession = Depends(get_db)):
    # Get the most recently published recommendation
    stmt = (
        select(Recommendation)
        .where(Recommendation.status.in_(["published", "published_with_warning"]))
        .order_by(Recommendation.published_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    rec = result.scalar_one_or_none()

    current_recommendation = None
    if rec:
        # Count weights
        weight_count_stmt = (
            select(func.count())
            .select_from(RecommendationWeight)
            .where(RecommendationWeight.recommendation_id == rec.id)
        )
        weight_count = (await db.execute(weight_count_stmt)).scalar() or 0

        # Get top overweight / underweight
        weights_stmt = (
            select(RecommendationWeight)
            .where(RecommendationWeight.recommendation_id == rec.id)
            .order_by(RecommendationWeight.delta.desc().nulls_last())
        )
        weights = (await db.execute(weights_stmt)).scalars().all()

        top_over = None
        top_under = None
        if weights:
            for w in weights:
                if w.stance == "overweight" and top_over is None:
                    top_over = w.asset_id
                if w.stance == "underweight" and top_under is None:
                    top_under = w.asset_id

        warning_list = rec.warnings if isinstance(rec.warnings, list) else []

        current_recommendation = RecommendationSummary(
            id=rec.id,
            status=rec.status,
            confidence=ConfidenceTriplet(
                model_confidence=rec.model_confidence,
                data_confidence=rec.data_confidence,
                operational_confidence=rec.operational_confidence,
            ),
            total_positions=weight_count,
            top_overweight=top_over,
            top_underweight=top_under,
            published_at=rec.published_at,
            valid_from=rec.valid_from,
            valid_to=rec.valid_to,
            data_as_of=rec.data_as_of,
            rationale_summary=rec.rationale_summary,
            warning_count=len(warning_list),
        )

    # Count total published recommendations
    total_stmt = (
        select(func.count())
        .select_from(Recommendation)
        .where(Recommendation.status.in_(["published", "published_with_warning"]))
    )
    total_count = (await db.execute(total_stmt)).scalar() or 0

    overview = OverviewResponse(
        current_recommendation=current_recommendation,
        health=HealthSummary(),
        recent_recommendation_count=total_count,
        last_published_at=rec.published_at if rec else None,
    )

    return ApiResponse(meta=make_meta(), data=overview)
