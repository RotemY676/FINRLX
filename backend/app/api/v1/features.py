"""Feature layer endpoints.

POST /api/v1/features/compute        — trigger feature computation
GET  /api/v1/features/status         — feature layer status summary
GET  /api/v1/features/latest         — latest completed feature set
GET  /api/v1/features/{feature_set_id} — single feature set with values
GET  /api/v1/features/definitions    — list feature definitions
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import make_meta
from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.feature import (
    FeatureComputeRequest,
    FeatureComputeResult,
    FeatureDefinitionResponse,
    FeatureSetResponse,
    FeatureStatusResponse,
    FeatureValueResponse,
)
from app.services.features import FeatureService

router = APIRouter()


@router.post("/features/compute", response_model=ApiResponse[FeatureComputeResult])
async def compute_features(
    body: FeatureComputeRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = FeatureService(db)
    fs = await svc.compute_features(
        universe_id=body.universe_id,
        as_of=body.as_of,
    )
    return ApiResponse(
        meta=make_meta(warnings=fs.warnings),
        data=FeatureComputeResult(
            feature_set_id=fs.id,
            status=fs.status,
            asset_count=fs.asset_count,
            feature_count=fs.feature_count,
            completeness_score=fs.completeness_score,
            warnings=fs.warnings or [],
            message=f"Computed {fs.feature_count} features for {fs.asset_count} assets "
                    f"(completeness {fs.completeness_score:.0%})",
        ),
    )


@router.get("/features/status", response_model=ApiResponse[FeatureStatusResponse])
async def get_feature_status(db: AsyncSession = Depends(get_db)):
    svc = FeatureService(db)
    status = await svc.get_status()
    return ApiResponse(
        meta=make_meta(),
        data=FeatureStatusResponse(**status),
    )


@router.get("/features/definitions", response_model=ApiResponse[list[FeatureDefinitionResponse]])
async def list_feature_definitions(db: AsyncSession = Depends(get_db)):
    svc = FeatureService(db)
    await svc.ensure_default_definitions()
    from sqlalchemy import select

    from app.models.feature import FeatureDefinition
    rows = (await db.execute(select(FeatureDefinition).order_by(FeatureDefinition.category))).scalars().all()
    items = [
        FeatureDefinitionResponse(
            id=d.id, key=d.key, name=d.name, category=d.category,
            description=d.description, version=d.version,
            lookback_days=d.lookback_days, input_kind=d.input_kind,
            output_type=d.output_type, is_active=d.is_active,
        )
        for d in rows
    ]
    return ApiResponse(meta=make_meta(), data=items)


@router.get("/features/latest", response_model=ApiResponse[FeatureSetResponse | None])
async def get_latest_feature_set(db: AsyncSession = Depends(get_db)):
    svc = FeatureService(db)
    fs = await svc.get_latest_feature_set()
    if not fs:
        return ApiResponse(meta=make_meta(), data=None)
    values = await svc.get_feature_values(fs.id)
    return ApiResponse(
        meta=make_meta(),
        data=FeatureSetResponse(
            id=fs.id, universe_id=fs.universe_id, as_of=fs.as_of,
            status=fs.status, feature_version=fs.feature_version,
            asset_count=fs.asset_count, feature_count=fs.feature_count,
            completeness_score=fs.completeness_score,
            freshness_status=fs.freshness_status,
            warnings=fs.warnings,
            started_at=fs.started_at, completed_at=fs.completed_at,
            values=[
                FeatureValueResponse(
                    asset_id=v.asset_id, ticker=v.ticker,
                    feature_key=v.feature_key, value=v.value,
                    unit=v.unit, window_days=v.window_days, quality=v.quality,
                )
                for v in values
            ],
        ),
    )


@router.get("/features/{feature_set_id}", response_model=ApiResponse[FeatureSetResponse])
async def get_feature_set(feature_set_id: str, db: AsyncSession = Depends(get_db)):
    svc = FeatureService(db)
    fs = await svc.get_feature_set(feature_set_id)
    if not fs:
        raise HTTPException(status_code=404, detail=f"Feature set {feature_set_id} not found")
    values = await svc.get_feature_values(fs.id)
    return ApiResponse(
        meta=make_meta(),
        data=FeatureSetResponse(
            id=fs.id, universe_id=fs.universe_id, as_of=fs.as_of,
            status=fs.status, feature_version=fs.feature_version,
            asset_count=fs.asset_count, feature_count=fs.feature_count,
            completeness_score=fs.completeness_score,
            freshness_status=fs.freshness_status,
            warnings=fs.warnings,
            started_at=fs.started_at, completed_at=fs.completed_at,
            values=[
                FeatureValueResponse(
                    asset_id=v.asset_id, ticker=v.ticker,
                    feature_key=v.feature_key, value=v.value,
                    unit=v.unit, window_days=v.window_days, quality=v.quality,
                )
                for v in values
            ],
        ),
    )
