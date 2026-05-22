"""Phase O-0 — operator console API.

Single-user (operator) endpoints that:
* persist LLM responses the operator pastes back from ChatGPT / Claude,
* list past responses (optionally filtered by recommendation_id), and
* expose them so the Replay view can surface them as "Analyst notes."

Gated by the `operator_console` feature flag (default OFF). The endpoints
are auth-required regardless; the flag prevents the surface from rendering
in the FE chrome for non-operator deployments.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_deps import get_current_user
from app.api.deps import make_meta
from app.core.config import settings
from app.core.database import get_db
from app.models.auth import User
from app.models.operator import (
    OPERATOR_ANALYSIS_SOURCES,
    OPERATOR_ANALYSIS_SURFACES,
    OperatorAnalysis,
)
from app.schemas.common import ApiResponse

router = APIRouter()


class OperatorAnalysisCreate(BaseModel):
    surface: str = Field(..., max_length=40)
    recommendation_id: str | None = Field(default=None, max_length=36)
    source: str = Field(default="other", max_length=20)
    prompt: str | None = Field(default=None, max_length=20000)
    response: str = Field(..., min_length=1, max_length=200000)
    note: str | None = Field(default=None, max_length=4000)


class OperatorAnalysisResponse(BaseModel):
    id: str
    user_email: str
    surface: str
    recommendation_id: str | None
    source: str
    prompt: str | None
    response: str
    note: str | None
    created_at: str


def _to_response(row: OperatorAnalysis) -> OperatorAnalysisResponse:
    return OperatorAnalysisResponse(
        id=row.id,
        user_email=row.user_email,
        surface=row.surface,
        recommendation_id=row.recommendation_id,
        source=row.source,
        prompt=row.prompt,
        response=row.response,
        note=row.note,
        created_at=row.created_at.isoformat() if row.created_at else "",
    )


def _gate_flag() -> None:
    if not settings.feature_operator_console:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="operator console disabled",
        )


@router.post(
    "/operator/analyses",
    response_model=ApiResponse[OperatorAnalysisResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_analysis(
    payload: OperatorAnalysisCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[OperatorAnalysisResponse]:
    _gate_flag()
    if payload.surface not in OPERATOR_ANALYSIS_SURFACES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"surface must be one of {OPERATOR_ANALYSIS_SURFACES}",
        )
    if payload.source not in OPERATOR_ANALYSIS_SOURCES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"source must be one of {OPERATOR_ANALYSIS_SOURCES}",
        )
    row = OperatorAnalysis(
        user_id=user.id,
        user_email=user.email,
        surface=payload.surface,
        recommendation_id=payload.recommendation_id,
        source=payload.source,
        prompt=payload.prompt,
        response=payload.response,
        note=payload.note,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return ApiResponse(meta=make_meta(), data=_to_response(row))


@router.get(
    "/operator/analyses",
    response_model=ApiResponse[list[OperatorAnalysisResponse]],
)
async def list_analyses(
    recommendation_id: str | None = Query(default=None, max_length=36),
    surface: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=100, ge=1, le=500),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[OperatorAnalysisResponse]]:
    _gate_flag()
    stmt = (
        select(OperatorAnalysis)
        .where(OperatorAnalysis.user_id == user.id)
        .order_by(OperatorAnalysis.created_at.desc())
        .limit(limit)
    )
    if recommendation_id:
        stmt = (
            select(OperatorAnalysis)
            .where(OperatorAnalysis.user_id == user.id)
            .where(OperatorAnalysis.recommendation_id == recommendation_id)
            .order_by(OperatorAnalysis.created_at.desc())
            .limit(limit)
        )
    if surface:
        stmt = stmt.where(OperatorAnalysis.surface == surface)
    rows = (await db.execute(stmt)).scalars().all()
    return ApiResponse(meta=make_meta(), data=[_to_response(r) for r in rows])


@router.delete(
    "/operator/analyses/{analysis_id}",
    response_model=ApiResponse[dict],
)
async def delete_analysis(
    analysis_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    _gate_flag()
    row = await db.get(OperatorAnalysis, analysis_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    await db.delete(row)
    await db.commit()
    return ApiResponse(meta=make_meta(), data={"deleted": analysis_id})
