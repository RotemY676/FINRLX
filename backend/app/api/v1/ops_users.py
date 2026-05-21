"""Phase BETA-3 — per-user usage summary for the /ops admin surface.

GET /api/v1/ops/users -> for each user (admin-only):
  - email, id, role, is_active, created_at, last_login_at
  - has_profile (bool)
  - profile_version (int or null)
  - paper_portfolio_count (int)
  - feedback_count (int)

Drives the BETA-3 dashboard. No tester ever sees this.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_deps import get_current_user
from app.api.deps import make_meta
from app.core.database import get_db
from app.models.auth import User
from app.models.feedback import Feedback
from app.models.profile import InvestorProfile
from app.models.validation import PaperPortfolio
from app.schemas.common import ApiResponse

router = APIRouter()


class UserUsageRow(BaseModel):
    id: str
    email: str
    role: str
    is_active: bool
    created_at: str | None
    last_login_at: str | None
    has_profile: bool
    profile_version: int | None
    paper_portfolio_count: int
    feedback_count: int


@router.get("/ops/users", response_model=ApiResponse[list[UserUsageRow]])
async def list_user_usage(
    limit: int = Query(default=200, ge=1, le=1000),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[UserUsageRow]]:
    if (user.role or "user").lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin role required",
        )

    users = (
        await db.execute(
            select(User).order_by(User.created_at.desc()).limit(limit)
        )
    ).scalars().all()

    if not users:
        return ApiResponse(meta=make_meta(), data=[])

    user_ids = [u.id for u in users]

    # Aggregated counts in 3 cheap queries
    profile_rows = (
        await db.execute(
            select(InvestorProfile.user_id, InvestorProfile.version).where(
                InvestorProfile.user_id.in_(user_ids)
            )
        )
    ).all()
    profile_by_user: dict[str, int] = {r.user_id: r.version for r in profile_rows}

    portfolio_rows = (
        await db.execute(
            select(PaperPortfolio.user_id, func.count())
            .where(PaperPortfolio.user_id.in_(user_ids))
            .group_by(PaperPortfolio.user_id)
        )
    ).all()
    portfolio_count_by_user: dict[str, int] = {
        r[0]: int(r[1]) for r in portfolio_rows
    }

    feedback_rows = (
        await db.execute(
            select(Feedback.user_id, func.count())
            .where(Feedback.user_id.in_(user_ids))
            .group_by(Feedback.user_id)
        )
    ).all()
    feedback_count_by_user: dict[str, int] = {
        r[0]: int(r[1]) for r in feedback_rows
    }

    out: list[UserUsageRow] = []
    for u in users:
        out.append(
            UserUsageRow(
                id=u.id,
                email=u.email,
                role=u.role or "user",
                is_active=u.is_active,
                created_at=u.created_at.isoformat() if u.created_at else None,
                last_login_at=u.last_login_at.isoformat()
                if u.last_login_at else None,
                has_profile=u.id in profile_by_user,
                profile_version=profile_by_user.get(u.id),
                paper_portfolio_count=portfolio_count_by_user.get(u.id, 0),
                feedback_count=feedback_count_by_user.get(u.id, 0),
            )
        )

    return ApiResponse(meta=make_meta(), data=out)
