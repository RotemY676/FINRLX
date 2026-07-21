"""Runtime inventory endpoint (US-P0-01) — operator/admin only.

GET /api/v1/ops/runtime-inventory returns a machine-readable manifest of the
running service (routes + auth level, feature flags, provider presence, schema
contracts, runtime pins) so the current baseline can be diffed against the
specification and discrepancies logged.

Restricted to the established privileged role (`admin`), matching the
feedback / ops_jobs / ops_users pattern. The manifest never exposes secrets,
keys, tokens, or the database URL.
"""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.auth_deps import get_current_user
from app.api.deps import make_meta
from app.core.config import settings
from app.models.auth import User
from app.schemas.common import ApiResponse
from app.schemas.inventory import RuntimeInventory
from app.services.runtime_inventory import build_runtime_inventory

router = APIRouter()


@router.get("/ops/runtime-inventory", response_model=ApiResponse[RuntimeInventory])
async def get_runtime_inventory(
    request: Request,
    user: User = Depends(get_current_user),
):
    if (user.role or "user").lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="admin role required"
        )

    inventory = build_runtime_inventory(
        app=request.app, settings=settings, now=datetime.now(UTC)
    )
    return ApiResponse(meta=make_meta(), data=inventory)
