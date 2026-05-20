"""ML model registry endpoints.

GET  /api/v1/models/definitions
GET  /api/v1/models/status
POST /api/v1/models/train
POST /api/v1/models/predict
GET  /api/v1/models/runs
GET  /api/v1/models/predictions
"""
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import make_meta
from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.modeling import (
    ModelDefinitionResponse,
    ModelPredictionResponse,
    ModelPredictRequest,
    ModelRunResponse,
    ModelStatusResponse,
    ModelTrainRequest,
)
from app.services.modeling import ModelingService

router = APIRouter()


@router.get("/models/definitions", response_model=ApiResponse[list[ModelDefinitionResponse]])
async def list_definitions(db: AsyncSession = Depends(get_db)):
    svc = ModelingService(db)
    await svc.ensure_default_definitions()
    defs = await svc.get_definitions()
    return ApiResponse(meta=make_meta(), data=[
        ModelDefinitionResponse(
            id=d.id, key=d.key, name=d.name, category=d.category,
            description=d.description, model_type=d.model_type,
            target=d.target, feature_keys=d.feature_keys,
            prediction_horizon_days=d.prediction_horizon_days,
            version=d.version, status=d.status, is_shadow=d.is_shadow,
        ) for d in defs
    ])


@router.get("/models/status", response_model=ApiResponse[ModelStatusResponse])
async def get_status(db: AsyncSession = Depends(get_db)):
    svc = ModelingService(db)
    await svc.ensure_default_definitions()
    status = await svc.get_status()
    return ApiResponse(meta=make_meta(), data=ModelStatusResponse(**status))


@router.post("/models/train", response_model=ApiResponse[ModelRunResponse])
async def train_model(body: ModelTrainRequest, db: AsyncSession = Depends(get_db)):
    svc = ModelingService(db)
    start = date.fromisoformat(body.train_start_date) if body.train_start_date else None
    end = date.fromisoformat(body.train_end_date) if body.train_end_date else None
    run = await svc.train_baseline(body.model_key, start, end)
    return ApiResponse(
        meta=make_meta(warnings=run.warnings),
        data=ModelRunResponse(
            id=run.id, model_key=run.model_key, run_type=run.run_type,
            status=run.status, metrics=run.metrics, warnings=run.warnings,
            started_at=run.started_at, completed_at=run.completed_at,
        ),
    )


@router.post("/models/predict", response_model=ApiResponse[ModelRunResponse])
async def predict(body: ModelPredictRequest, db: AsyncSession = Depends(get_db)):
    svc = ModelingService(db)
    run = await svc.predict(body.model_key, body.feature_set_id)
    return ApiResponse(
        meta=make_meta(warnings=run.warnings),
        data=ModelRunResponse(
            id=run.id, model_key=run.model_key, run_type=run.run_type,
            status=run.status, metrics=run.metrics, warnings=run.warnings,
            started_at=run.started_at, completed_at=run.completed_at,
        ),
    )


@router.get("/models/runs", response_model=ApiResponse[list[ModelRunResponse]])
async def list_runs(db: AsyncSession = Depends(get_db)):
    svc = ModelingService(db)
    runs = await svc.get_runs()
    return ApiResponse(meta=make_meta(), data=[
        ModelRunResponse(
            id=r.id, model_key=r.model_key, run_type=r.run_type,
            status=r.status, metrics=r.metrics, warnings=r.warnings,
            started_at=r.started_at, completed_at=r.completed_at,
        ) for r in runs
    ])


@router.get("/models/predictions", response_model=ApiResponse[list[ModelPredictionResponse]])
async def list_predictions(db: AsyncSession = Depends(get_db)):
    svc = ModelingService(db)
    preds = await svc.get_predictions()
    return ApiResponse(meta=make_meta(), data=[
        ModelPredictionResponse(
            asset_id=p.asset_id, ticker=p.ticker, as_of=p.as_of,
            prediction_value=p.prediction_value, prediction_score=p.prediction_score,
            confidence=p.confidence, quality=p.quality, drivers=p.drivers,
        ) for p in preds
    ])
