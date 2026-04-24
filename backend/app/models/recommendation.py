"""Recommendation and publication entities.

Maps to Data Model doc 11, Domain 6: Recommendation and Publication.
The Recommendation is the canonical output of the entire decision pipeline.
"""
from datetime import datetime

from sqlalchemy import DateTime, String, Text, Float, Enum, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, gen_uuid

import enum


class PublicationStatus(str, enum.Enum):
    DRAFT = "draft"
    STAGED = "staged"
    APPROVED = "approved"
    PUBLISHED = "published"
    PUBLISHED_WITH_WARNING = "published_with_warning"
    DEFERRED = "deferred"
    SUPPRESSED = "suppressed"
    SUPERSEDED = "superseded"
    STALE = "stale"
    RETIRED = "retired"


class Recommendation(Base, TimestampMixin):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    universe_id: Mapped[str] = mapped_column(String(36), nullable=False)

    # Publication state (doc 14 governance)
    status: Mapped[str] = mapped_column(
        String(30), default=PublicationStatus.DRAFT.value, nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Confidence triplet (doc 05 CDR, doc 09 functional reqs)
    model_confidence: Mapped[float | None] = mapped_column(Float)
    data_confidence: Mapped[float | None] = mapped_column(Float)
    operational_confidence: Mapped[float | None] = mapped_column(Float)

    # Recommendation window
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Rationale and warnings
    rationale_summary: Mapped[str | None] = mapped_column(Text)
    warnings: Mapped[dict | None] = mapped_column(JSON)

    # Policy reference
    policy_version_id: Mapped[str | None] = mapped_column(String(36))

    # Freshness
    data_as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Pipeline lineage (Phase 4D)
    source_feature_set_id: Mapped[str | None] = mapped_column(String(36))
    source_signal_run_ids: Mapped[list | None] = mapped_column(JSON)

    # Context isolation (Phase 5A+B.1): "live" or "backtest"
    context: Mapped[str] = mapped_column(String(20), default="live")


class RecommendationWeight(Base):
    """Per-asset target weight within a recommendation."""
    __tablename__ = "recommendation_weights"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    recommendation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    asset_id: Mapped[str] = mapped_column(String(36), nullable=False)

    target_weight: Mapped[float] = mapped_column(Float, nullable=False)
    previous_weight: Mapped[float | None] = mapped_column(Float)
    delta: Mapped[float | None] = mapped_column(Float)

    # Per-asset stance
    stance: Mapped[str | None] = mapped_column(String(30))  # overweight, underweight, neutral, exit
    rationale: Mapped[str | None] = mapped_column(Text)
