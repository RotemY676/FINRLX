"""Phase OP-2 — /ops/jobs endpoints.

Two endpoints:

  * GET  /api/v1/ops/jobs                  — recent JobRun rows
  * POST /api/v1/ops/jobs/{job_key}/run    — manual trigger

Manual trigger is admin-only (same role pattern as Phase TPL-4).
The GET endpoint requires authentication but no role gate so a beta
tester can audit the runs they care about.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_deps import get_current_user
from app.api.deps import make_meta
from app.core.database import get_db
from app.jobs.daily_dag import DAILY_DAG, run_single_job
from app.models.auth import User
from app.models.jobs import JobRun
from app.schemas.common import ApiResponse
from app.services.job_runs import JobRunService

router = APIRouter()


def _run_to_dict(run: JobRun) -> dict:
    return {
        "id": run.id,
        "job_key": run.job_key,
        "status": run.status,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "duration_ms": run.duration_ms,
        "triggered_by": run.triggered_by,
        "summary": run.summary,
        "error": run.error,
    }


@router.get("/ops/jobs", response_model=ApiResponse[dict])
async def list_job_runs(
    job_key: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    svc = JobRunService(db)
    runs = await svc.list_recent(job_key=job_key, limit=limit)
    known_jobs = [k for k, _ in DAILY_DAG]
    return ApiResponse(
        meta=make_meta(),
        data={
            "known_jobs": known_jobs,
            "runs": [_run_to_dict(r) for r in runs],
        },
    )


@router.post("/ops/jobs/{job_key}/run", response_model=ApiResponse[dict])
async def trigger_job(
    job_key: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    if (user.role or "user").lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin role required",
        )
    try:
        result = await run_single_job(db, job_key, triggered_by=f"manual:{user.id}")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ApiResponse(meta=make_meta(), data=result)
