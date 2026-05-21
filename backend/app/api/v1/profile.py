"""Phase W-2 — investor profile API.

Endpoints:

* ``GET  /api/v1/profile/questions``    — catalog grouped by step.
* ``GET  /api/v1/profile/me``           — current user's profile (or null).
* ``POST /api/v1/profile``              — submit wizard answers; computes
                                          risk_score + risk_bucket and
                                          persists profile + revision.
* ``GET  /api/v1/profile/revisions/me`` — current user's revision history.

All endpoints require auth via ``get_current_user``. There is no
admin / cross-user access — profiles are strictly per-tenant.
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
from app.models.profile import (
    InvestorProfile,
    InvestorProfileRevision,
    ProfileQuestion,
)
from app.schemas.common import ApiResponse
from app.schemas.profile import (
    InvestorProfileResponse,
    InvestorProfileSubmit,
    ProfileMeResponse,
    ProfileQuestionChoice,
    ProfileQuestionResponse,
    ProfileRevisionResponse,
    ProfileStepResponse,
)
from app.services.profile import (
    ProfileService,
    ProfileValidationError,
    score_answers,
)

router = APIRouter()


STEP_METADATA: dict[int, tuple[str, str]] = {
    2: ("Knowledge & experience", "knowledge"),
    3: ("Financial situation", "financial"),
    4: ("Risk tolerance", "risk"),
    5: ("Investment objectives", "objectives"),
    6: ("Universe & sector preferences", "universe"),
    7: ("Operational preferences", "operational"),
}


def _profile_to_response(p: InvestorProfile) -> InvestorProfileResponse:
    return InvestorProfileResponse(
        id=p.id,
        user_id=p.user_id,
        version=p.version,
        risk_score=p.risk_score,
        risk_bucket=p.risk_bucket,
        horizon_band=p.horizon_band,
        primary_goal=p.primary_goal,
        max_drawdown_pct=p.max_drawdown_pct,
        knowledge_level=p.knowledge_level,
        years_investing=p.years_investing,
        instruments_traded=json.loads(p.instruments_traded_json or "[]"),
        investable_amount_band=p.investable_amount_band,
        income_band=p.income_band,
        liquid_net_worth_band=p.liquid_net_worth_band,
        sector_whitelist=json.loads(p.sector_whitelist_json or "[]"),
        sector_blacklist=json.loads(p.sector_blacklist_json or "[]"),
        region_preference=p.region_preference,
        exclude_leverage=p.exclude_leverage,
        base_currency=p.base_currency,
        trading_frequency=p.trading_frequency,
        completed_at=p.completed_at,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _revision_to_response(r: InvestorProfileRevision) -> ProfileRevisionResponse:
    return ProfileRevisionResponse(
        id=r.id,
        profile_id=r.profile_id,
        user_id=r.user_id,
        version=r.version,
        change_summary=r.change_summary,
        created_at=r.created_at,
    )


@router.get(
    "/profile/questions",
    response_model=ApiResponse[list[ProfileStepResponse]],
)
async def get_profile_questions(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[ProfileStepResponse]]:
    rows = (
        await db.execute(
            select(ProfileQuestion)
            .where(ProfileQuestion.is_active)
            .order_by(ProfileQuestion.step, ProfileQuestion.order_in_step)
        )
    ).scalars().all()

    grouped: dict[int, list[ProfileQuestionResponse]] = {}
    for q in rows:
        choices = [
            ProfileQuestionChoice(**c) for c in json.loads(q.choices_json or "[]")
        ]
        grouped.setdefault(q.step, []).append(
            ProfileQuestionResponse(
                code=q.code,
                step=q.step,
                order_in_step=q.order_in_step,
                dimension=q.dimension,
                text=q.text,
                helper_text=q.helper_text,
                choices=choices,
                is_required=q.is_required,
                is_active=q.is_active,
            )
        )

    steps: list[ProfileStepResponse] = []
    for step in sorted(grouped.keys()):
        label, hint = STEP_METADATA.get(step, (f"Step {step}", "general"))
        steps.append(
            ProfileStepResponse(
                step=step,
                label=label,
                dimension_hint=hint,
                questions=grouped[step],
            )
        )
    return ApiResponse(meta=make_meta(), data=steps)


@router.get("/profile/me", response_model=ApiResponse[ProfileMeResponse])
async def get_my_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ProfileMeResponse]:
    service = ProfileService(db)
    profile = await service.get_current(user.id)
    body = ProfileMeResponse(
        has_profile=profile is not None,
        profile=_profile_to_response(profile) if profile is not None else None,
    )
    return ApiResponse(meta=make_meta(), data=body)


@router.post(
    "/profile",
    response_model=ApiResponse[InvestorProfileResponse],
    status_code=status.HTTP_201_CREATED,
)
async def submit_profile(
    payload: InvestorProfileSubmit,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[InvestorProfileResponse]:
    service = ProfileService(db)
    risk_choices = await service.load_risk_question_choices()
    if not risk_choices:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="profile_questions catalog is not seeded",
        )
    try:
        scored = score_answers(payload.answers, risk_choices)
    except ProfileValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    profile = await service.upsert(
        user_id=user.id,
        scored=scored,
        raw_answers=payload.answers,
        change_summary=payload.change_summary,
    )
    return ApiResponse(meta=make_meta(), data=_profile_to_response(profile))


@router.get(
    "/profile/revisions/me",
    response_model=ApiResponse[list[ProfileRevisionResponse]],
)
async def list_my_revisions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[ProfileRevisionResponse]]:
    service = ProfileService(db)
    rows = await service.list_revisions(user.id)
    return ApiResponse(
        meta=make_meta(), data=[_revision_to_response(r) for r in rows]
    )
