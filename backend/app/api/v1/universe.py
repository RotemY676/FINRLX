"""Universe management endpoints.

GET    /api/v1/universes
POST   /api/v1/universes                    (Phase 20)
GET    /api/v1/universes/default
GET    /api/v1/universes/{universe_id}
PATCH  /api/v1/universes/{universe_id}      (Phase 20)
DELETE /api/v1/universes/{universe_id}      (Phase 20 — soft, sets is_active=false)
GET    /api/v1/universes/{universe_id}/coverage
GET    /api/v1/universes/{universe_id}/readiness
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import make_meta
from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.universe import UniverseCreateRequest, UniverseUpdateRequest
from app.services.universe import (
    UniverseConflictError,
    UniverseNotFoundError,
    UniverseService,
)

router = APIRouter()


@router.get("/universes", response_model=ApiResponse[list[dict]])
async def list_universes(db: AsyncSession = Depends(get_db)):
    svc = UniverseService(db)
    return ApiResponse(meta=make_meta(), data=await svc.get_universes())


@router.post("/universes", response_model=ApiResponse[dict], status_code=201)
async def create_universe(
    body: UniverseCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = UniverseService(db)
    try:
        data = await svc.create_universe(body.name, body.description)
    except UniverseConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return ApiResponse(meta=make_meta(), data=data)


@router.patch("/universes/{universe_id}", response_model=ApiResponse[dict])
async def update_universe(
    universe_id: str,
    body: UniverseUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = UniverseService(db)
    try:
        data = await svc.update_universe(
            universe_id,
            name=body.name,
            description=body.description,
            is_active=body.is_active,
        )
    except UniverseNotFoundError:
        raise HTTPException(status_code=404, detail="Universe not found")
    except UniverseConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return ApiResponse(meta=make_meta(), data=data)


@router.delete("/universes/{universe_id}", response_model=ApiResponse[dict])
async def deactivate_universe(
    universe_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete — sets is_active=false. The row is preserved so historical
    recommendations and backtests stay replayable. There is no hard-delete
    endpoint in Phase 20."""
    svc = UniverseService(db)
    try:
        data = await svc.deactivate_universe(universe_id)
    except UniverseNotFoundError:
        raise HTTPException(status_code=404, detail="Universe not found")
    except UniverseConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return ApiResponse(meta=make_meta(), data=data)


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
