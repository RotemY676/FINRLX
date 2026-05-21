"""Phase TPL-2 — recommendation-template read API.

Endpoints (read-only in TPL-2; TPL-4 adds admin CRUD):

* ``GET /api/v1/templates``        — list active templates (auth-required).
* ``GET /api/v1/templates/{key}``  — one template by slug.

Every response embeds the W-4-derived expected metrics. Metrics are
computed on the fly (cheap pure function); we don't cache them on the
row in this sub-phase.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_deps import get_current_user
from app.api.deps import make_meta
from app.core.database import get_db
from app.models.auth import User
from app.models.recommendation_template import RecommendationTemplate
from app.schemas.common import ApiResponse
from app.schemas.template import (
    RecommendationTemplateCreate,
    RecommendationTemplateResponse,
    RecommendationTemplateUpdate,
    TemplateMetricsResponse,
)
from app.services.profile_mapping import (
    AllocationMappingError,
    derive_allocation,
)
from app.services.template_metrics import expected_metrics

router = APIRouter()


def _require_admin(user: User) -> None:
    """Phase TPL-4 — admin-role gate. Inline because this is the only
    surface in the codebase that needs it; promote to a shared dep when
    a second consumer arrives.
    """
    if (user.role or "user").lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin role required",
        )


def _allocation_summary(risk_bucket: str, horizon: str) -> str | None:
    try:
        targets = derive_allocation(risk_bucket, horizon)
    except AllocationMappingError:
        return None
    return f"{int(round(targets.equity_pct))}/{int(round(targets.defensive_pct))}"


def _to_response(t: RecommendationTemplate) -> RecommendationTemplateResponse:
    metrics = expected_metrics(t)
    return RecommendationTemplateResponse(
        id=t.id,
        key=t.key,
        name=t.name,
        description=t.description,
        badge=t.badge,
        risk_bucket=t.risk_bucket,
        horizon_band=t.horizon_band,
        primary_goal=t.primary_goal,
        max_drawdown_pct=t.max_drawdown_pct,
        sector_whitelist=json.loads(t.sector_whitelist_json or "[]"),
        sector_blacklist=json.loads(t.sector_blacklist_json or "[]"),
        exclude_leverage=t.exclude_leverage,
        base_currency=t.base_currency,
        trading_frequency=t.trading_frequency,
        region_preference=t.region_preference,
        is_seed=t.is_seed,
        is_active=t.is_active,
        allocation_summary=t.allocation_summary,
        metrics=TemplateMetricsResponse(**metrics.__dict__),
    )


@router.get(
    "/templates",
    response_model=ApiResponse[list[RecommendationTemplateResponse]],
)
async def list_templates(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[RecommendationTemplateResponse]]:
    rows = (
        await db.execute(
            select(RecommendationTemplate)
            .where(RecommendationTemplate.is_active)
            .order_by(
                RecommendationTemplate.is_seed.desc(),
                RecommendationTemplate.name,
            )
        )
    ).scalars().all()
    return ApiResponse(meta=make_meta(), data=[_to_response(t) for t in rows])


@router.get(
    "/templates/{key}",
    response_model=ApiResponse[RecommendationTemplateResponse],
)
async def get_template(
    key: str,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[RecommendationTemplateResponse]:
    t = (
        await db.execute(
            select(RecommendationTemplate).where(RecommendationTemplate.key == key)
        )
    ).scalar_one_or_none()
    if t is None or not t.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"template {key!r} not found"
        )
    return ApiResponse(meta=make_meta(), data=_to_response(t))


# ── Phase TPL-4 — admin CRUD ─────────────────────────────────────────


@router.post(
    "/templates",
    response_model=ApiResponse[RecommendationTemplateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_template(
    payload: RecommendationTemplateCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[RecommendationTemplateResponse]:
    _require_admin(user)

    existing = (
        await db.execute(
            select(RecommendationTemplate).where(
                RecommendationTemplate.key == payload.key
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"template key {payload.key!r} already exists",
        )

    # Validate the (bucket, horizon) pair early — same surface as the
    # apply-template path uses internally.
    try:
        derive_allocation(payload.risk_bucket, payload.horizon_band)
    except AllocationMappingError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    new = RecommendationTemplate(
        key=payload.key,
        name=payload.name,
        description=payload.description,
        badge=payload.badge,
        risk_bucket=payload.risk_bucket,
        horizon_band=payload.horizon_band,
        primary_goal=payload.primary_goal,
        max_drawdown_pct=payload.max_drawdown_pct,
        sector_whitelist_json=json.dumps(payload.sector_whitelist),
        sector_blacklist_json=json.dumps(payload.sector_blacklist),
        exclude_leverage=payload.exclude_leverage,
        base_currency=payload.base_currency,
        trading_frequency=payload.trading_frequency,
        region_preference=payload.region_preference,
        is_seed=False,
        is_active=True,
        created_by_user_id=user.id,
        allocation_summary=_allocation_summary(
            payload.risk_bucket, payload.horizon_band
        ),
    )
    db.add(new)
    await db.commit()
    await db.refresh(new)
    return ApiResponse(meta=make_meta(), data=_to_response(new))


@router.put(
    "/templates/{key}",
    response_model=ApiResponse[RecommendationTemplateResponse],
)
async def update_template(
    key: str,
    payload: RecommendationTemplateUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[RecommendationTemplateResponse]:
    _require_admin(user)

    template = (
        await db.execute(
            select(RecommendationTemplate).where(RecommendationTemplate.key == key)
        )
    ).scalar_one_or_none()
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"template {key!r} not found",
        )
    if template.is_seed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="seed templates are immutable; create a new one instead",
        )

    updates = payload.model_dump(exclude_unset=True)
    if "sector_whitelist" in updates:
        template.sector_whitelist_json = json.dumps(updates.pop("sector_whitelist"))
    if "sector_blacklist" in updates:
        template.sector_blacklist_json = json.dumps(updates.pop("sector_blacklist"))
    for field, value in updates.items():
        setattr(template, field, value)

    # Refresh allocation_summary if the bucket or horizon changed.
    if "risk_bucket" in updates or "horizon_band" in updates:
        try:
            derive_allocation(template.risk_bucket, template.horizon_band)
        except AllocationMappingError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        template.allocation_summary = _allocation_summary(
            template.risk_bucket, template.horizon_band
        )

    await db.commit()
    await db.refresh(template)
    return ApiResponse(meta=make_meta(), data=_to_response(template))


@router.delete(
    "/templates/{key}",
    response_model=ApiResponse[dict],
)
async def delete_template(
    key: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    _require_admin(user)

    template = (
        await db.execute(
            select(RecommendationTemplate).where(RecommendationTemplate.key == key)
        )
    ).scalar_one_or_none()
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"template {key!r} not found",
        )
    if template.is_seed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="seed templates cannot be deleted; deactivate via PUT instead",
        )

    await db.delete(template)
    await db.commit()
    return ApiResponse(meta=make_meta(), data={"key": key, "deleted": True})
