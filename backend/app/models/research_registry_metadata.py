"""Research registry metadata mirror — Postgres-backed sanitized summary."""
from datetime import datetime
from sqlalchemy import DateTime, String, Text, Boolean, JSON, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, gen_uuid


class ResearchRegistryMetadata(Base, TimestampMixin):
    """Mirror of sanitized research registry metadata.

    This is NOT the operational registry — local JSON registries remain
    the primary source.  This table stores sanitized metadata summaries
    for durability, operator visibility, and future migration readiness.

    Research-only, offline-only, no production influence.
    """

    __tablename__ = "research_registry_metadata"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    registry_kind: Mapped[str] = mapped_column(String(50), nullable=False)
    record_id: Mapped[str] = mapped_column(String(100), nullable=False)
    record_hash: Mapped[str | None] = mapped_column(String(200), nullable=True)
    record_state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    source_registry_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    artifact_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_summary_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    warnings_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    limitations_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    mirror_status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    research_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    offline_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    no_production_influence: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("registry_kind", "record_id", name="uq_registry_kind_record_id"),
        Index("ix_rrm_registry_kind", "registry_kind"),
        Index("ix_rrm_record_id", "record_id"),
        Index("ix_rrm_mirror_status", "mirror_status"),
        Index("ix_rrm_last_seen_at", "last_seen_at"),
    )
