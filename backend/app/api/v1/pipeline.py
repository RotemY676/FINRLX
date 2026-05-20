"""Decision pipeline endpoints.

POST /api/v1/pipeline/run              — trigger full pipeline run
GET  /api/v1/pipeline/status           — pipeline status summary
GET  /api/v1/pipeline/latest           — latest pipeline-generated recommendation
GET  /api/v1/pipeline/runs             — list pipeline runs
GET  /api/v1/pipeline/runs/{rec_id}    — pipeline run detail with stages
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import make_meta
from app.core.database import get_db
from app.models.recommendation import RecommendationWeight
from app.models.reference import Asset
from app.schemas.common import ApiResponse
from app.schemas.pipeline import (
    PipelineRunRequest,
    PipelineRunResult,
    PipelineStageResult,
    PipelineStatusResponse,
)
from app.schemas.recommendation import ConfidenceTriplet, RecommendationDetail, WeightEntry
from app.services.pipeline import DecisionPipelineService

router = APIRouter()


@router.post("/pipeline/run", response_model=ApiResponse[PipelineRunResult])
async def run_pipeline(body: PipelineRunRequest, db: AsyncSession = Depends(get_db)):
    svc = DecisionPipelineService(db)
    result = await svc.run_pipeline(
        signal_run_ids=body.signal_run_ids,
        universe_id=body.universe_id,
        feature_set_id=body.feature_set_id,
        include_shadow_engines=body.include_shadow_engines,
    )
    return ApiResponse(
        meta=make_meta(warnings=result.get("warnings")),
        data=PipelineRunResult(
            recommendation_id=result["recommendation_id"],
            status=result["status"],
            stages=[PipelineStageResult(**s) for s in result["stages"]],
            warnings=result.get("warnings", []),
            feature_set_id=result.get("feature_set_id"),
            signal_run_ids=result.get("signal_run_ids"),
            message=result["message"],
        ),
    )


@router.get("/pipeline/status", response_model=ApiResponse[PipelineStatusResponse])
async def get_pipeline_status(db: AsyncSession = Depends(get_db)):
    svc = DecisionPipelineService(db)
    status = await svc.get_status()
    return ApiResponse(meta=make_meta(), data=PipelineStatusResponse(**status))


@router.get("/pipeline/runs", response_model=ApiResponse[list[dict]])
async def list_pipeline_runs(db: AsyncSession = Depends(get_db)):
    svc = DecisionPipelineService(db)
    runs = await svc.get_pipeline_runs()
    return ApiResponse(meta=make_meta(), data=runs)


@router.get("/pipeline/runs/{recommendation_id}", response_model=ApiResponse[dict])
async def get_pipeline_run_detail(recommendation_id: str, db: AsyncSession = Depends(get_db)):
    svc = DecisionPipelineService(db)
    detail = await svc.get_pipeline_run_detail(recommendation_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    return ApiResponse(meta=make_meta(), data=detail)


@router.get("/pipeline/latest", response_model=ApiResponse[RecommendationDetail | None])
async def get_latest_pipeline_recommendation(db: AsyncSession = Depends(get_db)):
    svc = DecisionPipelineService(db)
    rec = await svc.get_latest_pipeline_recommendation()
    if not rec:
        return ApiResponse(meta=make_meta(warnings=["No pipeline-generated recommendation"]), data=None)

    # Build detail
    weights_stmt = (
        select(RecommendationWeight, Asset.ticker, Asset.name)
        .outerjoin(Asset, RecommendationWeight.asset_id == Asset.id)
        .where(RecommendationWeight.recommendation_id == rec.id)
        .order_by(RecommendationWeight.target_weight.desc())
    )
    rows = (await db.execute(weights_stmt)).all()
    weight_entries = [
        WeightEntry(
            asset_id=w.asset_id, ticker=ticker or "???", name=name or "Unknown",
            target_weight=w.target_weight, previous_weight=w.previous_weight,
            delta=w.delta, stance=w.stance, rationale=w.rationale,
        )
        for w, ticker, name in rows
    ]

    return ApiResponse(
        meta=make_meta(),
        data=RecommendationDetail(
            id=rec.id, status=rec.status,
            confidence=ConfidenceTriplet(
                model_confidence=rec.model_confidence,
                data_confidence=rec.data_confidence,
                operational_confidence=rec.operational_confidence,
            ),
            weights=weight_entries,
            published_at=rec.published_at,
            valid_from=rec.valid_from, valid_to=rec.valid_to,
            data_as_of=rec.data_as_of,
            rationale_summary=rec.rationale_summary,
            warnings=rec.warnings if isinstance(rec.warnings, list) else [],
            policy_version_id=rec.policy_version_id,
            created_at=rec.created_at,
        ),
    )
