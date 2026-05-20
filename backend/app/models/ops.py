"""Admin, ops, and governance entities.

Maps to Data Model doc 11, Domain 8: Admin, Ops, Governance.
"""
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, gen_uuid


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    object_type: Mapped[str | None] = mapped_column(String(100))
    object_id: Mapped[str | None] = mapped_column(String(36))
    details: Mapped[dict | None] = mapped_column(JSON)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Incident(Base, TimestampMixin):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    severity: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-4
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="open")  # open, acknowledged, resolved
    source: Mapped[str | None] = mapped_column(String(100))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SystemHealthSnapshot(Base):
    __tablename__ = "system_health_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    source_freshness: Mapped[dict | None] = mapped_column(JSON)
    feature_health: Mapped[dict | None] = mapped_column(JSON)
    model_health: Mapped[dict | None] = mapped_column(JSON)
    publication_health: Mapped[dict | None] = mapped_column(JSON)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class DataFeed(Base):
    __tablename__ = "data_feeds"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ok")  # ok, degraded, stale
    lag: Mapped[str] = mapped_column(String(30), default="0s")
    coverage: Mapped[str] = mapped_column(String(20), default="100%")
    slo: Mapped[float] = mapped_column(Float, default=1.0)
    last_checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PolicyBreach(Base, TimestampMixin):
    __tablename__ = "policy_breaches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)  # sector, single, oil, etc.
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    utilization: Mapped[float] = mapped_column(Float, nullable=False)
    trend: Mapped[str] = mapped_column(String(30), default="+0%")
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # high, mid, breach
    related: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class PublicationQueueEntry(Base, TimestampMixin):
    __tablename__ = "publication_queue"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    recommendation_id: Mapped[str] = mapped_column(String(50), nullable=False)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    stance: Mapped[str] = mapped_column(String(20), nullable=False)
    version: Mapped[str] = mapped_column(String(10), default="v1")
    submitter: Mapped[str] = mapped_column(String(100), nullable=False)
    weight: Mapped[str] = mapped_column(String(30), default="0%")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    flags: Mapped[list | None] = mapped_column(JSON, default=list)
    priority: Mapped[str] = mapped_column(String(10), default="mid")  # high, mid, low
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, approved, deferred
    submitted_ago: Mapped[str] = mapped_column(String(30), default="")
