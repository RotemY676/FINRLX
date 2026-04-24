"""Signal and engine output entities.

Maps to Data Model doc 11, Domain 4: Signal and Engine Outputs.
"""
from datetime import datetime

from sqlalchemy import DateTime, String, Text, Float, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, gen_uuid


class SignalRun(Base, TimestampMixin):
    __tablename__ = "signal_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    engine_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    engine_version: Mapped[str | None] = mapped_column(String(50))
    feature_set_id: Mapped[str | None] = mapped_column(String(36))
    run_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    run_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="completed")
    data_as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SignalOutput(Base, TimestampMixin):
    __tablename__ = "signal_outputs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    signal_run_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    asset_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    score: Mapped[float | None] = mapped_column(Float)
    stance: Mapped[str | None] = mapped_column(String(30))  # bullish, bearish, neutral
    confidence: Mapped[float | None] = mapped_column(Float)
    rationale: Mapped[str | None] = mapped_column(Text)
    artifacts: Mapped[dict | None] = mapped_column(JSON)
