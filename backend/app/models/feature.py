"""Feature registry and computed feature set entities.

Maps to Data Model doc 11, Domain 3: Feature Registry.

Tables:
  feature_definitions — named feature recipes with version and config
  feature_sets        — computed feature batches with completeness and freshness
  feature_values      — individual computed feature values per asset per feature
"""
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, gen_uuid


class FeatureDefinition(Base, TimestampMixin):
    __tablename__ = "feature_definitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    key: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # momentum, volatility, volume, sentiment, drawdown
    description: Mapped[str | None] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")
    lookback_days: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    input_kind: Mapped[str] = mapped_column(String(20), nullable=False, default="bars")  # bars, news, mixed
    output_type: Mapped[str] = mapped_column(String(20), nullable=False, default="float")  # float, int, label
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class FeatureSet(Base, TimestampMixin):
    __tablename__ = "feature_sets"
    __table_args__ = (
        Index("ix_feature_set_as_of", "as_of"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    universe_id: Mapped[str | None] = mapped_column(String(36))
    as_of: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending, computing, completed, partial, failed
    feature_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")
    source_manifest_ids: Mapped[list | None] = mapped_column(JSON)
    asset_count: Mapped[int] = mapped_column(Integer, default=0)
    feature_count: Mapped[int] = mapped_column(Integer, default=0)
    completeness_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0.0 to 1.0
    freshness_status: Mapped[str] = mapped_column(String(20), default="unknown")  # healthy, stale, degraded, unknown
    warnings: Mapped[list | None] = mapped_column(JSON)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FeatureValue(Base):
    __tablename__ = "feature_values"
    __table_args__ = (
        Index("ix_fv_set_asset", "feature_set_id", "asset_id"),
        Index("ix_fv_set_key", "feature_set_id", "feature_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    feature_set_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    asset_id: Mapped[str] = mapped_column(String(36), nullable=False)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    feature_key: Mapped[str] = mapped_column(String(80), nullable=False)
    value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(20))  # pct, ratio, count, score
    window_days: Mapped[int | None] = mapped_column(Integer)
    quality: Mapped[str] = mapped_column(String(30), nullable=False, default="ok")  # ok, insufficient_data, stale, missing
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
