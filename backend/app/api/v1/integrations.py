"""Integrations endpoints.

GET /api/v1/integrations
GET /api/v1/integrations/health
GET /api/v1/integrations/{source_key}
GET /api/v1/integrations/readiness
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.services.integrations import IntegrationsService

router = APIRouter()


@router.get("/integrations", response_model=ApiResponse[list[dict]])
async def list_integrations(db: AsyncSession = Depends(get_db)):
    svc = IntegrationsService(db)
    return ApiResponse(meta=make_meta(), data=await svc.get_integrations())


@router.get("/integrations/health", response_model=ApiResponse[dict])
async def get_integration_health(db: AsyncSession = Depends(get_db)):
    svc = IntegrationsService(db)
    return ApiResponse(meta=make_meta(), data=await svc.get_integration_health())


@router.get("/integrations/readiness", response_model=ApiResponse[dict])
async def get_provider_readiness(db: AsyncSession = Depends(get_db)):
    svc = IntegrationsService(db)
    return ApiResponse(meta=make_meta(), data=await svc.get_provider_readiness())


@router.get("/integrations/{source_key}", response_model=ApiResponse[dict | None])
async def get_integration_detail(source_key: str, db: AsyncSession = Depends(get_db)):
    svc = IntegrationsService(db)
    detail = await svc.get_integration_detail(source_key)
    if not detail:
        raise HTTPException(status_code=404, detail="Integration not found")
    return ApiResponse(meta=make_meta(), data=detail)
