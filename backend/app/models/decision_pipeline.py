"""Decision pipeline stage entities.

Maps to Data Model doc 11, Domain 5: Decision Pipeline.
Isolates selection, allocation, timing, and risk overlay into separate tables.
"""
from datetime import datetime

from sqlalchemy import DateTime, String, Text, Float, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, gen_uuid


class SelectionRun(Base, TimestampMixin):
    __tablename__ = "selection_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    recommendation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    universe_id: Mapped[str] = mapped_column(String(36), nullable=False)

    included_assets: Mapped[dict | None] = mapped_column(JSON)  # [{asset_id, reason}]
    excluded_assets: Mapped[dict | None] = mapped_column(JSON)  # [{asset_id, reason}]
    rationale: Mapped[str | None] = mapped_column(Text)


class AllocationResult(Base, TimestampMixin):
    __tablename__ = "allocation_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    recommendation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    selection_run_id: Mapped[str] = mapped_column(String(36), nullable=False)

    weights: Mapped[dict | None] = mapped_column(JSON)  # {asset_id: weight}
    method: Mapped[str | None] = mapped_column(String(100))
    rationale: Mapped[str | None] = mapped_column(Text)


class TimingResult(Base, TimestampMixin):
    __tablename__ = "timing_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    recommendation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    urgency: Mapped[str | None] = mapped_column(String(30))  # immediate, soon, wait, defer
    horizon_days: Mapped[int | None] = mapped_column()
    entry_signals: Mapped[dict | None] = mapped_column(JSON)
    exit_signals: Mapped[dict | None] = mapped_column(JSON)
    rationale: Mapped[str | None] = mapped_column(Text)


class RiskOverlayResult(Base, TimestampMixin):
    __tablename__ = "risk_overlay_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    recommendation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    pre_risk_weights: Mapped[dict | None] = mapped_column(JSON)
    post_risk_weights: Mapped[dict | None] = mapped_column(JSON)
    adjustments: Mapped[dict | None] = mapped_column(JSON)  # [{asset_id, reason, delta}]
    constraints_applied: Mapped[dict | None] = mapped_column(JSON)
    portfolio_risk_score: Mapped[float | None] = mapped_column(Float)
    rationale: Mapped[str | None] = mapped_column(Text)
