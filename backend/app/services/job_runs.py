"""Phase OP-2 — JobRun persistence + simple "with run_lifecycle" helper.

`record_job` is a context manager that:
  * inserts a JobRun row with status=open at start
  * on success → status=completed + summary
  * on exception → status=failed + error message
  * always sets finished_at + duration_ms

Used by every entry in `app.jobs.daily_dag` to make job runs durable
without each job re-implementing try/except + DB writes.
"""
from __future__ import annotations

import time
import traceback
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.jobs import (
    JOB_STATUS_COMPLETED,
    JOB_STATUS_FAILED,
    JobRun,
)


def _duration_ms_safe(
    start: datetime | None, end: datetime | None
) -> int | None:
    """SQLite stores DateTime(timezone=True) as naive UTC; Postgres
    preserves tz. Coerce to a comparable form before subtracting.
    """
    if start is None or end is None:
        return None
    s = start if start.tzinfo is not None else start.replace(tzinfo=UTC)
    e = end if end.tzinfo is not None else end.replace(tzinfo=UTC)
    return int((e - s).total_seconds() * 1000.0)


class JobRunService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_open(self, job_key: str, triggered_by: str = "schedule") -> JobRun:
        run = JobRun(job_key=job_key, triggered_by=triggered_by)
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def mark_completed(self, run: JobRun, summary: str | None) -> JobRun:
        run.status = JOB_STATUS_COMPLETED
        run.finished_at = datetime.now(UTC)
        run.summary = summary
        run.duration_ms = _duration_ms_safe(run.started_at, run.finished_at)
        await self.db.commit()
        return run

    async def mark_failed(self, run: JobRun, error: str) -> JobRun:
        run.status = JOB_STATUS_FAILED
        run.finished_at = datetime.now(UTC)
        run.error = error[:2000]
        run.duration_ms = _duration_ms_safe(run.started_at, run.finished_at)
        await self.db.commit()
        return run

    async def list_recent(
        self, job_key: str | None = None, limit: int = 50
    ) -> list[JobRun]:
        stmt = select(JobRun).order_by(JobRun.started_at.desc()).limit(limit)
        if job_key:
            stmt = select(JobRun).where(JobRun.job_key == job_key).order_by(
                JobRun.started_at.desc()
            ).limit(limit)
        return list((await self.db.execute(stmt)).scalars().all())


@asynccontextmanager
async def record_job(
    db: AsyncSession, job_key: str, triggered_by: str = "schedule"
) -> AsyncIterator[JobRun]:
    """Context manager that wraps a job invocation in a JobRun row.

    Usage::

        async with record_job(db, "my_job") as run:
            ...  # do work
            run.summary = "ok 42 things"
    """
    svc = JobRunService(db)
    run = await svc.create_open(job_key, triggered_by=triggered_by)
    started = time.perf_counter()
    try:
        yield run
    except Exception:  # noqa: BLE001 — we deliberately swallow to record
        err = traceback.format_exc()
        await svc.mark_failed(run, err)
        raise
    else:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        if run.duration_ms is None:
            run.duration_ms = elapsed_ms
        await svc.mark_completed(run, run.summary)
