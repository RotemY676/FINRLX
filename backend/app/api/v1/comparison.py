"""Comparison endpoint.

GET /api/v1/comparison/current — compares current recommendation vs equal-weight benchmark.
Maps to API Contract doc 12, Engine Comparison.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import make_meta
from app.core.database import get_db
from app.models.recommendation import Recommendation, RecommendationWeight
from app.models.reference import Asset
from app.schemas.common import ApiResponse
from app.schemas.comparison import ComparisonResponse, ComparisonWeightRow
from app.schemas.recommendation import ConfidenceTriplet

router = APIRouter()


@router.get("/comparison/current", response_model=ApiResponse[ComparisonResponse | None])
async def get_current_comparison(db: AsyncSession = Depends(get_db)):
    # Get current published recommendation
    stmt = (
        select(Recommendation)
        .where(Recommendation.status.in_(["published", "published_with_warning"]))
        .order_by(Recommendation.published_at.desc())
        .limit(1)
    )
    rec = (await db.execute(stmt)).scalar_one_or_none()
    if not rec:
        return ApiResponse(
            meta=make_meta(warnings=["No published recommendation"]),
            data=None,
        )

    # Get weights with asset info
    weights_stmt = (
        select(RecommendationWeight, Asset.ticker, Asset.name)
        .outerjoin(Asset, RecommendationWeight.asset_id == Asset.id)
        .where(RecommendationWeight.recommendation_id == rec.id)
        .order_by(RecommendationWeight.target_weight.desc())
    )
    rows = (await db.execute(weights_stmt)).all()
    n_assets = len(rows)
    equal_weight = 1.0 / n_assets if n_assets > 0 else 0

    comparison_rows = []
    for w, ticker, name in rows:
        delta = w.target_weight - equal_weight
        comparison_rows.append(ComparisonWeightRow(
            asset_id=w.asset_id,
            ticker=ticker or "???",
            name=name or "Unknown",
            recommendation_weight=w.target_weight,
            benchmark_weight=round(equal_weight, 4),
            delta=round(delta, 4),
            recommendation_stance=w.stance,
        ))

    total_active = sum(abs(r.delta) for r in comparison_rows)

    sorted_by_rec = sorted(comparison_rows, key=lambda r: r.recommendation_weight, reverse=True)
    sorted_by_bench = sorted(comparison_rows, key=lambda r: r.benchmark_weight, reverse=True)
    top3_rec = sum(r.recommendation_weight for r in sorted_by_rec[:3])
    top3_bench = sum(r.benchmark_weight for r in sorted_by_bench[:3])

    warning_list = rec.warnings if isinstance(rec.warnings, list) else []

    return ApiResponse(
        meta=make_meta(),
        data=ComparisonResponse(
            recommendation_id=rec.id,
            benchmark_name="Equal Weight",
            recommendation_confidence=ConfidenceTriplet(
                model_confidence=rec.model_confidence,
                data_confidence=rec.data_confidence,
                operational_confidence=rec.operational_confidence,
            ),
            weights=comparison_rows,
            recommendation_warning_count=len(warning_list),
            recommendation_rationale=rec.rationale_summary,
            total_active_weight=round(total_active, 4),
            concentration_top3_rec=round(top3_rec, 4),
            concentration_top3_bench=round(top3_bench, 4),
        ),
    )
