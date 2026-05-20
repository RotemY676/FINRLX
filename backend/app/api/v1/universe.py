"""Universe management endpoints.

GET /api/v1/universes
GET /api/v1/universes/default
GET /api/v1/universes/{universe_id}
GET /api/v1/universes/{universe_id}/coverage
GET /api/v1/universes/{universe_id}/readiness
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import make_meta
from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.services.universe import UniverseService

router = APIRouter()


@router.get("/universes", response_model=ApiResponse[list[dict]])
async def list_universes(db: AsyncSession = Depends(get_db)):
    svc = UniverseService(db)
    return ApiResponse(meta=make_meta(), data=await svc.get_universes())


@router.get("/universes/default", response_model=ApiResponse[dict | None])
async def get_default_universe(db: AsyncSession = Depends(get_db)):
    svc = UniverseService(db)
    data = await svc.get_default_universe()
    if not data:
        return ApiResponse(meta=make_meta(warnings=["No universe exists"]), data=None)
    return ApiResponse(meta=make_meta(), data=data)


@router.get("/universes/{universe_id}", response_model=ApiResponse[dict])
async def get_universe(universe_id: str, db: AsyncSession = Depends(get_db)):
    svc = UniverseService(db)
    data = await svc.get_universe_detail(universe_id)
    if not data:
        raise HTTPException(status_code=404, detail="Universe not found")
    return ApiResponse(meta=make_meta(), data=data)


@router.get("/universes/{universe_id}/coverage", response_model=ApiResponse[dict])
async def get_universe_coverage(universe_id: str, db: AsyncSession = Depends(get_db)):
    svc = UniverseService(db)
    return ApiResponse(meta=make_meta(), data=await svc.get_asset_coverage(universe_id))


@router.get("/universes/{universe_id}/readiness", response_model=ApiResponse[dict])
async def get_universe_readiness(universe_id: str, db: AsyncSession = Depends(get_db)):
    svc = UniverseService(db)
    return ApiResponse(meta=make_meta(), data=await svc.get_universe_readiness(universe_id))
