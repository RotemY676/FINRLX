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
    meta_warnings = []

    # Get the most recently published recommendation (live context only)
    rec = (await db.execute(
        select(Recommendation)
        .where(Recommendation.status.in_(["published", "published_with_warning"]))
        .where(Recommendation.context != "backtest")
        .order_by(Recommendation.published_at.desc())
        .limit(1)
    )).scalar_one_or_none()

    # Check for newer pipeline draft (live context only)
    latest_draft = (await db.execute(
        select(Recommendation)
        .where(Recommendation.source_feature_set_id.is_not(None))
        .where(Recommendation.context != "backtest")
        .order_by(Recommendation.created_at.desc())
        .limit(1)
    )).scalar_one_or_none()

    # If no published rec but draft exists, use the draft
    if not rec and latest_draft:
        rec = latest_draft
        meta_warnings.append(
            "No published recommendation exists; showing latest pipeline-generated draft."
        )
    elif rec and latest_draft and latest_draft.id != rec.id:
        if latest_draft.created_at and rec.created_at and latest_draft.created_at > rec.created_at:
            meta_warnings.append(
                "A newer pipeline-generated draft exists but is not published yet."
            )

    current_recommendation = None
    if rec:
        weight_count = (await db.execute(
            select(func.count()).select_from(RecommendationWeight)
            .where(RecommendationWeight.recommendation_id == rec.id)
        )).scalar() or 0

        weights = (await db.execute(
            select(RecommendationWeight)
            .where(RecommendationWeight.recommendation_id == rec.id)
            .order_by(RecommendationWeight.delta.desc().nulls_last())
        )).scalars().all()

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

    total_count = (await db.execute(
        select(func.count()).select_from(Recommendation)
        .where(Recommendation.status.in_(["published", "published_with_warning"]))
    )).scalar() or 0

    overview = OverviewResponse(
        current_recommendation=current_recommendation,
        health=HealthSummary(),
        recent_recommendation_count=total_count,
        last_published_at=rec.published_at if rec else None,
    )

    return ApiResponse(
        meta=make_meta(warnings=meta_warnings if meta_warnings else None),
        data=overview,
    )
