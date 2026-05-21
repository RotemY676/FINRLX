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
    RecommendationTemplateResponse,
    TemplateMetricsResponse,
)
from app.services.template_metrics import expected_metrics

router = APIRouter()


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
