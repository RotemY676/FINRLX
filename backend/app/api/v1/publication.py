"""Publication workflow endpoints.

POST /api/v1/publication/recommendations/{id}/stage
POST /api/v1/publication/recommendations/{id}/approve
POST /api/v1/publication/recommendations/{id}/publish
POST /api/v1/publication/recommendations/{id}/defer
POST /api/v1/publication/recommendations/{id}/suppress
GET  /api/v1/publication/recommendations/{id}/gates
GET  /api/v1/publication/recommendations/{id}/history
GET  /api/v1/publication/status
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.schemas.publication import (
    PublicationGateResult, PublicationGateCheck,
    PublicationActionRequest, PublicationTransitionResponse,
    PublicationStatusResponse, PublicationHistoryEntry,
)
from app.services.publication import PublicationService

router = APIRouter()


def _to_transition_response(result: dict) -> PublicationTransitionResponse:
    return PublicationTransitionResponse(
        recommendation_id=result["recommendation_id"],
        previous_status=result["previous_status"],
        new_status=result["new_status"],
        allowed=result["allowed"],
        gates=[PublicationGateCheck(**g) for g in result["gates"]] if result.get("gates") else None,
        warnings=result.get("warnings", []),
        audit_event_id=result.get("audit_event_id"),
        message=result["message"],
    )


@router.get("/publication/status", response_model=ApiResponse[PublicationStatusResponse])
async def get_publication_status(db: AsyncSession = Depends(get_db)):
    svc = PublicationService(db)
    status = await svc.get_status()
    return ApiResponse(meta=make_meta(), data=PublicationStatusResponse(**status))


@router.get("/publication/recommendations/{rec_id}/gates", response_model=ApiResponse[PublicationGateResult])
async def get_gates(rec_id: str, db: AsyncSession = Depends(get_db)):
    svc = PublicationService(db)
    result = await svc.evaluate_gates(rec_id)
    return ApiResponse(
        meta=make_meta(),
        data=PublicationGateResult(
            recommendation_id=result["recommendation_id"],
            overall=result["overall"],
            gates=[PublicationGateCheck(**g) for g in result["gates"]],
            can_publish=result["can_publish"],
        ),
    )


@router.get("/publication/recommendations/{rec_id}/history", response_model=ApiResponse[list[PublicationHistoryEntry]])
async def get_history(rec_id: str, db: AsyncSession = Depends(get_db)):
    svc = PublicationService(db)
    history = await svc.get_history(rec_id)
    return ApiResponse(meta=make_meta(), data=[PublicationHistoryEntry(**h) for h in history])


@router.post("/publication/recommendations/{rec_id}/stage", response_model=ApiResponse[PublicationTransitionResponse])
async def stage_recommendation(rec_id: str, body: PublicationActionRequest, db: AsyncSession = Depends(get_db)):
    svc = PublicationService(db)
    result = await svc.stage(rec_id, body.actor, body.reason)
    return ApiResponse(meta=make_meta(), data=_to_transition_response(result))


@router.post("/publication/recommendations/{rec_id}/approve", response_model=ApiResponse[PublicationTransitionResponse])
async def approve_recommendation(rec_id: str, body: PublicationActionRequest, db: AsyncSession = Depends(get_db)):
    svc = PublicationService(db)
    result = await svc.approve(rec_id, body.actor, body.reason)
    return ApiResponse(meta=make_meta(), data=_to_transition_response(result))


@router.post("/publication/recommendations/{rec_id}/publish", response_model=ApiResponse[PublicationTransitionResponse])
async def publish_recommendation(rec_id: str, body: PublicationActionRequest, db: AsyncSession = Depends(get_db)):
    svc = PublicationService(db)
    result = await svc.publish(rec_id, body.actor, body.reason)
    return ApiResponse(meta=make_meta(), data=_to_transition_response(result))


@router.post("/publication/recommendations/{rec_id}/defer", response_model=ApiResponse[PublicationTransitionResponse])
async def defer_recommendation(rec_id: str, body: PublicationActionRequest, db: AsyncSession = Depends(get_db)):
    svc = PublicationService(db)
    if not body.reason:
        return ApiResponse(
            meta=make_meta(warnings=["Reason required for defer"]),
            data=PublicationTransitionResponse(
                recommendation_id=rec_id, previous_status="", new_status="",
                allowed=False, message="Reason is required for defer",
            ),
        )
    result = await svc.defer(rec_id, body.actor, body.reason)
    return ApiResponse(meta=make_meta(), data=_to_transition_response(result))


@router.post("/publication/recommendations/{rec_id}/suppress", response_model=ApiResponse[PublicationTransitionResponse])
async def suppress_recommendation(rec_id: str, body: PublicationActionRequest, db: AsyncSession = Depends(get_db)):
    svc = PublicationService(db)
    if not body.reason:
        return ApiResponse(
            meta=make_meta(warnings=["Reason required for suppress"]),
            data=PublicationTransitionResponse(
                recommendation_id=rec_id, previous_status="", new_status="",
                allowed=False, message="Reason is required for suppress",
            ),
        )
    result = await svc.suppress(rec_id, body.actor, body.reason)
    return ApiResponse(meta=make_meta(), data=_to_transition_response(result))
