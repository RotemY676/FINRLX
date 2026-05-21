"""Phase OP-2 — daily DAG of operational jobs.

The DAG is a flat list of independent jobs that run in order; each
records its own JobRun row, so a downstream failure doesn't lose the
provenance of the upstream success.

Jobs (job_key -> what it does):
  * ``daily_fx_refresh``     — Frankfurter -> fx_rates upsert via FxService
  * ``daily_fx_freshness``   — emit Incident rows when fx lag > threshold

Heavier ingestion/feature/signal jobs are wired here as placeholders —
they call existing service entry points so the DAG mirrors the real
pipeline. Each placeholder is best-effort: failures are captured in the
JobRun and the DAG continues.

The DAG entrypoint ``run_daily_dag(db)`` returns a summary dict that
both the CLI (`scripts.run_daily_dag`) and the `/api/v1/ops/jobs/...`
trigger endpoint render to the operator.
"""
from __future__ import annotations

from typing import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.fx_freshness import emit_incidents_if_stale, evaluate_freshness
from app.services.fx_service import FxService
from app.services.job_runs import record_job

JobFunc = Callable[[AsyncSession], Awaitable[str]]


async def job_daily_fx_refresh(db: AsyncSession) -> str:
    svc = FxService(db)
    result = await svc.refresh_rates_for_today()
    return f"fetched={result['fetched']} errors={result['errors']}"


async def job_daily_fx_freshness(db: AsyncSession) -> str:
    report = await evaluate_freshness(db)
    out = await emit_incidents_if_stale(db, report)
    return (
        f"evaluated_pairs={len(report.pairs)} "
        f"stale_pairs={len(report.stale_pairs)} "
        f"opened={out['opened']} skipped_existing={out['skipped_existing']}"
    )


# Order matters: refresh before freshness so the freshness watchdog
# never falsely opens an incident on the same run that would have
# refreshed the missing rate.
DAILY_DAG: list[tuple[str, JobFunc]] = [
    ("daily_fx_refresh", job_daily_fx_refresh),
    ("daily_fx_freshness", job_daily_fx_freshness),
]


async def run_daily_dag(
    db: AsyncSession, triggered_by: str = "schedule"
) -> dict:
    """Run every job in DAILY_DAG. Each job's failure is contained
    in its own JobRun; the DAG itself never re-raises.
    """
    completed: list[str] = []
    failed: list[str] = []

    for job_key, func in DAILY_DAG:
        try:
            async with record_job(db, job_key, triggered_by=triggered_by) as run:
                run.summary = await func(db)
            completed.append(job_key)
        except Exception as exc:  # noqa: BLE001 — DAG must not abort
            failed.append(f"{job_key}: {exc}")
            # record_job already persisted the failure; we just keep going.

    return {
        "jobs_total": len(DAILY_DAG),
        "completed": completed,
        "failed": failed,
    }


async def run_single_job(
    db: AsyncSession, job_key: str, triggered_by: str = "manual"
) -> dict:
    """Trigger one job by key. Useful for /ops/jobs/{key}/run."""
    target = next(((k, f) for k, f in DAILY_DAG if k == job_key), None)
    if target is None:
        raise ValueError(f"unknown job_key {job_key!r}")
    key, func = target
    try:
        async with record_job(db, key, triggered_by=triggered_by) as run:
            run.summary = await func(db)
        return {"job_key": key, "status": "completed", "summary": run.summary}
    except Exception as exc:  # noqa: BLE001
        return {"job_key": key, "status": "failed", "error": str(exc)}
