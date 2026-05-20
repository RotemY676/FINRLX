"""Action bar endpoints for the Decision Workspace.

Compatibility wrappers that route through PublicationService.

POST /api/v1/actions/save-thesis  — stages the latest recommendation (draft -> staged)
POST /api/v1/actions/promote-paper — defers with reason "promoted to paper"
POST /api/v1/actions/defer         — defers the latest recommendation
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import make_meta
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.recommendation import Recommendation
from app.schemas.action import ActionResult, DeferRequest
from app.schemas.common import ApiResponse
from app.services.publication import PublicationService

router = APIRouter()


async def _get_latest_rec(db: AsyncSession) -> Recommendation | None:
    result = await db.execute(
        select(Recommendation).order_by(Recommendation.created_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()


@router.post("/actions/save-thesis", response_model=ApiResponse[ActionResult])
@limiter.limit(settings.rate_limit_recommendation_write)
async def save_thesis(request: Request, db: AsyncSession = Depends(get_db)):
    rec = await _get_latest_rec(db)
    if not rec:
        return ApiResponse(
            meta=make_meta(warnings=["No recommendation found"]),
            data=ActionResult(action="save_thesis", success=False, new_status="", message="No recommendation to save"),
        )

    svc = PublicationService(db)
    result = await svc.stage(rec.id, "operator", "Saved as current thesis via action bar")

    return ApiResponse(
        meta=make_meta(),
        data=ActionResult(
            action="save_thesis", success=result["allowed"],
            new_status=result["new_status"],
            message=result["message"],
        ),
    )


@router.post("/actions/promote-paper", response_model=ApiResponse[ActionResult])
@limiter.limit(settings.rate_limit_recommendation_write)
async def promote_paper(request: Request, db: AsyncSession = Depends(get_db)):
    rec = await _get_latest_rec(db)
    if not rec:
        return ApiResponse(
            meta=make_meta(warnings=["No recommendation found"]),
            data=ActionResult(action="promote_paper", success=False, new_status="", message="No recommendation to promote"),
        )

    svc = PublicationService(db)
    result = await svc.defer(rec.id, "operator", "Promoted to paper portfolio for shadow tracking")

    return ApiResponse(
        meta=make_meta(),
        data=ActionResult(
            action="promote_paper", success=result["allowed"],
            new_status=result["new_status"],
            message=result["message"],
        ),
    )


@router.post("/actions/defer", response_model=ApiResponse[ActionResult])
@limiter.limit(settings.rate_limit_recommendation_write)
async def defer_decision(request: Request, body: DeferRequest | None = None, db: AsyncSession = Depends(get_db)):
    rec = await _get_latest_rec(db)
    if not rec:
        return ApiResponse(
            meta=make_meta(warnings=["No recommendation found"]),
            data=ActionResult(action="defer", success=False, new_status="", message="No recommendation to defer"),
        )

    reason = (body.reason if body and body.reason else "Deferred via action bar")
    svc = PublicationService(db)
    result = await svc.defer(rec.id, "operator", reason)

    return ApiResponse(
        meta=make_meta(),
        data=ActionResult(
            action="defer", success=result["allowed"],
            new_status=result["new_status"],
            message=result["message"],
        ),
    )
