"""Phase OP-2 — JobRun: persistent record of every scheduled-job execution.

One row per (job_key, started_at) so /ops/jobs can render the last N
runs per job and a re-run button can replay the same key. ``status``
moves open → completed | failed; ``error`` carries the last exception
when applicable.
"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import gen_uuid

JOB_STATUS_OPEN = "open"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"
JOB_STATUSES = (JOB_STATUS_OPEN, JOB_STATUS_COMPLETED, JOB_STATUS_FAILED)


class JobRun(Base):
    __tablename__ = "job_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    job_key: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=JOB_STATUS_OPEN, index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    triggered_by: Mapped[str] = mapped_column(String(40), nullable=False, default="schedule")
    error: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
