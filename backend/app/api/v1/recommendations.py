"""Recommendation endpoints.

GET /api/v1/recommendations/current
GET /api/v1/recommendations/{id}
Maps to API Contract doc 12.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.schemas.recommendation import RecommendationDetail, ConfidenceTriplet, WeightEntry
from app.models.recommendation import Recommendation, RecommendationWeight
from app.models.reference import Asset

router = APIRouter()


async def _build_recommendation_detail(
    rec: Recommendation, db: AsyncSession
) -> RecommendationDetail:
    weights_stmt = (
        select(RecommendationWeight, Asset.ticker, Asset.name)
        .outerjoin(Asset, RecommendationWeight.asset_id == Asset.id)
        .where(RecommendationWeight.recommendation_id == rec.id)
        .order_by(RecommendationWeight.target_weight.desc())
    )
    rows = (await db.execute(weights_stmt)).all()

    weight_entries = [
        WeightEntry(
            asset_id=w.asset_id,
            ticker=ticker or "???",
            name=name or "Unknown",
            target_weight=w.target_weight,
            previous_weight=w.previous_weight,
            delta=w.delta,
            stance=w.stance,
            rationale=w.rationale,
        )
        for w, ticker, name in rows
    ]

    warning_list = rec.warnings if isinstance(rec.warnings, list) else []

    return RecommendationDetail(
        id=rec.id,
        status=rec.status,
        confidence=ConfidenceTriplet(
            model_confidence=rec.model_confidence,
            data_confidence=rec.data_confidence,
            operational_confidence=rec.operational_confidence,
        ),
        weights=weight_entries,
        published_at=rec.published_at,
        valid_from=rec.valid_from,
        valid_to=rec.valid_to,
        data_as_of=rec.data_as_of,
        rationale_summary=rec.rationale_summary,
        warnings=warning_list,
        policy_version_id=rec.policy_version_id,
        created_at=rec.created_at,
    )


@router.get("/recommendations/current", response_model=ApiResponse[RecommendationDetail | None])
async def get_current_recommendation(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Recommendation)
        .where(Recommendation.status.in_(["published", "published_with_warning"]))
        .order_by(Recommendation.published_at.desc())
        .limit(1)
    )
    rec = (await db.execute(stmt)).scalar_one_or_none()

    if not rec:
        return ApiResponse(meta=make_meta(warnings=["No published recommendation found"]), data=None)

    detail = await _build_recommendation_detail(rec, db)
    return ApiResponse(meta=make_meta(), data=detail)


@router.get("/recommendations/{recommendation_id}", response_model=ApiResponse[RecommendationDetail])
async def get_recommendation_by_id(recommendation_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Recommendation).where(Recommendation.id == recommendation_id)
    rec = (await db.execute(stmt)).scalar_one_or_none()

    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    detail = await _build_recommendation_detail(rec, db)
    return ApiResponse(meta=make_meta(), data=detail)
