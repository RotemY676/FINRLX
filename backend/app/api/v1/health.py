"""System health endpoint.

GET /api/v1/health — system health summary.
Maps to API Contract doc 12, Admin & Ops.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import make_meta
from app.schemas.common import ApiResponse

router = APIRouter()


@router.get("/health")
async def api_health(db: AsyncSession = Depends(get_db)):
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    return ApiResponse(
        meta=make_meta(),
        data={
            "status": "ok" if db_ok else "degraded",
            "version": settings.app_version,
            "database": "connected" if db_ok else "unreachable",
        },
    )
