"""Phase BETA-2 — feedback API.

Endpoints:
* POST /api/v1/feedback      — tester submits feedback (auth required)
* GET  /api/v1/feedback      — admin lists all feedback (admin role)
* GET  /api/v1/feedback/me   — tester reads their own submissions
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_deps import get_current_user
from app.api.deps import make_meta
from app.core.database import get_db
from app.models.auth import User
from app.models.feedback import Feedback
from app.schemas.common import ApiResponse

router = APIRouter()


class FeedbackCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    surface: str | None = Field(default=None, max_length=100)
    category: str = Field(default="general", max_length=40)


class FeedbackResponse(BaseModel):
    id: str
    user_id: str
    user_email: str
    surface: str | None
    category: str
    message: str
    status: str
    created_at: str


def _to_response(f: Feedback) -> FeedbackResponse:
    return FeedbackResponse(
        id=f.id,
        user_id=f.user_id,
        user_email=f.user_email,
        surface=f.surface,
        category=f.category,
        message=f.message,
        status=f.status,
        created_at=f.created_at.isoformat() if f.created_at else "",
    )


@router.post(
    "/feedback",
    response_model=ApiResponse[FeedbackResponse],
    status_code=status.HTTP_201_CREATED,
)
async def submit_feedback(
    payload: FeedbackCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[FeedbackResponse]:
    row = Feedback(
        user_id=user.id,
        user_email=user.email,
        surface=payload.surface,
        category=payload.category or "general",
        message=payload.message,
        status="open",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return ApiResponse(meta=make_meta(), data=_to_response(row))


@router.get(
    "/feedback/me",
    response_model=ApiResponse[list[FeedbackResponse]],
)
async def list_my_feedback(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[FeedbackResponse]]:
    rows = (
        await db.execute(
            select(Feedback)
            .where(Feedback.user_id == user.id)
            .order_by(Feedback.created_at.desc())
        )
    ).scalars().all()
    return ApiResponse(meta=make_meta(), data=[_to_response(r) for r in rows])


@router.get(
    "/feedback",
    response_model=ApiResponse[list[FeedbackResponse]],
)
async def list_all_feedback(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=200, ge=1, le=1000),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[FeedbackResponse]]:
    if (user.role or "user").lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin role required",
        )
    stmt = select(Feedback).order_by(Feedback.created_at.desc()).limit(limit)
    if status_filter:
        stmt = (
            select(Feedback)
            .where(Feedback.status == status_filter)
            .order_by(Feedback.created_at.desc())
            .limit(limit)
        )
    rows = (await db.execute(stmt)).scalars().all()
    return ApiResponse(meta=make_meta(), data=[_to_response(r) for r in rows])
