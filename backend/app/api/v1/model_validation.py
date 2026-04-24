"""ML model validation endpoints.

POST /api/v1/models/validation/run
GET  /api/v1/models/validation/latest
GET  /api/v1/models/validation/history
GET  /api/v1/models/validation/{report_id}
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.services.ml_validation import MLValidationService
from app.models.modeling import ModelValidationReport

router = APIRouter()


def _report_dict(r: ModelValidationReport) -> dict:
    return {
        "id": r.id, "model_key": r.model_key, "model_version": r.model_version,
        "evaluated_at": r.evaluated_at, "horizon_days": r.horizon_days,
        "sample_count": r.sample_count, "status": r.status,
        "directional_accuracy": r.directional_accuracy,
        "mean_absolute_error": r.mean_absolute_error,
        "rank_correlation": r.rank_correlation,
        "hit_rate": r.hit_rate, "avg_confidence": r.avg_confidence,
        "calibration_error": r.calibration_error,
        "baseline_comparison": r.baseline_comparison,
        "confidence_buckets": r.confidence_buckets,
        "promotion_readiness": r.promotion_readiness,
        "warnings": r.warnings,
    }


@router.post("/models/validation/run", response_model=ApiResponse[dict])
async def run_validation(db: AsyncSession = Depends(get_db)):
    svc = MLValidationService(db)
    report = await svc.evaluate_shadow_model()
    return ApiResponse(meta=make_meta(warnings=report.warnings), data=_report_dict(report))


@router.get("/models/validation/latest", response_model=ApiResponse[dict | None])
async def get_latest_validation(db: AsyncSession = Depends(get_db)):
    svc = MLValidationService(db)
    report = await svc.get_latest_report("ml_return_forecaster")
    if not report:
        return ApiResponse(meta=make_meta(warnings=["No validation report exists"]), data=None)
    return ApiResponse(meta=make_meta(), data=_report_dict(report))


@router.get("/models/validation/history", response_model=ApiResponse[list[dict]])
async def get_validation_history(db: AsyncSession = Depends(get_db)):
    svc = MLValidationService(db)
    reports = await svc.get_history("ml_return_forecaster")
    return ApiResponse(meta=make_meta(), data=[_report_dict(r) for r in reports])


@router.get("/models/validation/{report_id}", response_model=ApiResponse[dict])
async def get_validation_report(report_id: str, db: AsyncSession = Depends(get_db)):
    report = (await db.execute(
        select(ModelValidationReport).where(ModelValidationReport.id == report_id)
    )).scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Validation report not found")
    return ApiResponse(meta=make_meta(), data=_report_dict(report))
