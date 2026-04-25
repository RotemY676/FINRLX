"""ML Ops observability endpoints.

GET /api/v1/ml-ops/summary
GET /api/v1/ml-ops/models/{model_key}
GET /api/v1/ml-ops/models/{model_key}/warnings
GET /api/v1/ml-ops/models/{model_key}/shadow-status
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.schemas.ml_ops import MLOpsSummaryResponse, MLOpsWarning
from app.services.ml_ops import MLOpsService

router = APIRouter()


@router.get("/ml-ops/summary", response_model=ApiResponse[MLOpsSummaryResponse])
async def get_ml_ops_summary(db: AsyncSession = Depends(get_db)):
    svc = MLOpsService(db)
    data = await svc.get_ml_ops_summary()
    return ApiResponse(meta=make_meta(), data=MLOpsSummaryResponse(**data))


@router.get("/ml-ops/models/{model_key}", response_model=ApiResponse[dict])
async def get_model_detail(model_key: str, db: AsyncSession = Depends(get_db)):
    svc = MLOpsService(db)
    health = await svc.get_model_health(model_key)
    validation = await svc.get_validation_summary(model_key)
    promotion = await svc.get_promotion_summary(model_key)
    shadow = await svc.get_shadow_status(model_key)
    return ApiResponse(meta=make_meta(), data={
        "health": health,
        "validation": validation,
        "promotion": promotion,
        "shadow": shadow,
    })


@router.get("/ml-ops/models/{model_key}/warnings", response_model=ApiResponse[list[MLOpsWarning]])
async def get_model_warnings(model_key: str, db: AsyncSession = Depends(get_db)):
    svc = MLOpsService(db)
    warnings = await svc.get_ml_warnings(model_key)
    return ApiResponse(meta=make_meta(), data=[MLOpsWarning(**w) for w in warnings])


@router.get("/ml-ops/models/{model_key}/shadow-status", response_model=ApiResponse[dict])
async def get_shadow_status(model_key: str, db: AsyncSession = Depends(get_db)):
    svc = MLOpsService(db)
    data = await svc.get_shadow_status(model_key)
    return ApiResponse(meta=make_meta(), data=data)
