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
    warnings = []

    # 1. Try published recommendation first (live context only)
    published = (await db.execute(
        select(Recommendation)
        .where(Recommendation.status.in_(["published", "published_with_warning"]))
        .where(Recommendation.context != "backtest")
        .order_by(Recommendation.published_at.desc())
        .limit(1)
    )).scalar_one_or_none()

    # 2. Check for newer pipeline-generated draft (live context only)
    latest_draft = (await db.execute(
        select(Recommendation)
        .where(Recommendation.source_feature_set_id.is_not(None))
        .where(Recommendation.context != "backtest")
        .order_by(Recommendation.created_at.desc())
        .limit(1)
    )).scalar_one_or_none()

    if published:
        # Published exists — use it, but warn if newer draft exists
        if latest_draft and latest_draft.id != published.id:
            if latest_draft.created_at and published.created_at:
                if latest_draft.created_at > published.created_at:
                    warnings.append(
                        "A newer pipeline-generated draft exists but is not published yet."
                    )
        detail = await _build_recommendation_detail(published, db)
        return ApiResponse(meta=make_meta(warnings=warnings if warnings else None), data=detail)

    if latest_draft:
        # No published, but draft exists — return it with warning
        warnings.append(
            "No published recommendation exists; returning latest pipeline-generated draft."
        )
        detail = await _build_recommendation_detail(latest_draft, db)
        return ApiResponse(meta=make_meta(warnings=warnings), data=detail)

    return ApiResponse(
        meta=make_meta(warnings=["No published recommendation found"]),
        data=None,
    )


@router.get("/recommendations/{recommendation_id}", response_model=ApiResponse[RecommendationDetail])
async def get_recommendation_by_id(recommendation_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Recommendation).where(Recommendation.id == recommendation_id)
    rec = (await db.execute(stmt)).scalar_one_or_none()

    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    detail = await _build_recommendation_detail(rec, db)
    return ApiResponse(meta=make_meta(), data=detail)
