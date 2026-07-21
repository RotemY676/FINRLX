"""Unified readiness endpoint (US-P0-08) — operator/admin only.

GET /api/v1/ops/readiness aggregates market-data, FX, and provider readiness
into one report with an overall verdict and the affected scope for anything not
ready. Fail-closed: unevaluable components report ``unavailable``.

Restricted to the established ``admin`` role — readiness detail (which tickers
are stale, which providers are degraded) is privileged operational evidence.
"""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_deps import get_current_user
from app.api.deps import make_meta
from app.core.database import get_db
from app.models.auth import User
from app.schemas.common import ApiResponse
from app.schemas.readiness import ReadinessReport
from app.services.readiness import build_readiness

router = APIRouter()


@router.get("/ops/readiness", response_model=ApiResponse[ReadinessReport])
async def get_readiness(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if (user.role or "user").lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="admin role required"
        )
    report = await build_readiness(db, now=datetime.now(UTC))
    return ApiResponse(meta=make_meta(), data=report)
