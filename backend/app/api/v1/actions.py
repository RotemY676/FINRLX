"""Action bar endpoints for the Decision Workspace.

POST /api/v1/actions/save-thesis      — save recommendation as current thesis
POST /api/v1/actions/promote-paper    — promote to paper portfolio
POST /api/v1/actions/defer            — defer decision
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.schemas.action import ActionResult, DeferRequest
from app.models.recommendation import Recommendation
from app.models.ops import AuditEvent

router = APIRouter()


async def _get_latest_rec(db: AsyncSession) -> Recommendation | None:
    result = await db.execute(
        select(Recommendation).order_by(Recommendation.created_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()


async def _audit(db: AsyncSession, action: str, description: str) -> None:
    db.add(AuditEvent(
        actor="current_user",
        action=action,
        object_type="recommendation",
        details={"description": description, "ago": "now"},
        occurred_at=datetime.now(timezone.utc),
    ))


@router.post("/actions/save-thesis", response_model=ApiResponse[ActionResult])
async def save_thesis(db: AsyncSession = Depends(get_db)):
    rec = await _get_latest_rec(db)
    if not rec:
        return ApiResponse(
            meta=make_meta(warnings=["No recommendation found"]),
            data=ActionResult(action="save_thesis", success=False, new_status="", message="No recommendation to save"),
        )

    rec.status = "staged"
    await _audit(db, "save_thesis", f"Saved recommendation as current thesis")
    await db.commit()

    return ApiResponse(
        meta=make_meta(),
        data=ActionResult(action="save_thesis", success=True, new_status="staged", message="Recommendation saved as current thesis"),
    )


@router.post("/actions/promote-paper", response_model=ApiResponse[ActionResult])
async def promote_paper(db: AsyncSession = Depends(get_db)):
    rec = await _get_latest_rec(db)
    if not rec:
        return ApiResponse(
            meta=make_meta(warnings=["No recommendation found"]),
            data=ActionResult(action="promote_paper", success=False, new_status="", message="No recommendation to promote"),
        )

    previous_status = rec.status
    rec.status = "paper"
    await _audit(db, "promote_paper", f"Promoted recommendation to paper portfolio (was {previous_status})")
    await db.commit()

    return ApiResponse(
        meta=make_meta(),
        data=ActionResult(action="promote_paper", success=True, new_status="paper", message="Recommendation promoted to paper portfolio"),
    )


@router.post("/actions/defer", response_model=ApiResponse[ActionResult])
async def defer_decision(body: DeferRequest | None = None, db: AsyncSession = Depends(get_db)):
    rec = await _get_latest_rec(db)
    if not rec:
        return ApiResponse(
            meta=make_meta(warnings=["No recommendation found"]),
            data=ActionResult(action="defer", success=False, new_status="", message="No recommendation to defer"),
        )

    rec.status = "deferred"
    reason = (body.reason if body and body.reason else "No reason given")
    await _audit(db, "defer", f"Deferred decision: {reason}")
    await db.commit()

    return ApiResponse(
        meta=make_meta(),
        data=ActionResult(action="defer", success=True, new_status="deferred", message=f"Decision deferred: {reason}"),
    )
