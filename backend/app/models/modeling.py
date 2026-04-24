"""ML model registry entities.

Phase 6A: model definitions, runs, and predictions.
"""
from datetime import datetime, date

from sqlalchemy import Date, DateTime, Float, Integer, String, Text, JSON, Boolean, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, gen_uuid


class ModelDefinition(Base, TimestampMixin):
    __tablename__ = "model_definitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    key: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # ml, statistical, baseline
    description: Mapped[str | None] = mapped_column(Text)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False, default="baseline_linear")
    target: Mapped[str] = mapped_column(String(100), nullable=False, default="forward_return_20d")
    feature_keys: Mapped[list | None] = mapped_column(JSON)
    prediction_horizon_days: Mapped[int] = mapped_column(Integer, default=20)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="experimental")
    is_shadow: Mapped[bool] = mapped_column(Boolean, default=True)


class ModelRun(Base):
    __tablename__ = "model_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    model_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")
    run_type: Mapped[str] = mapped_column(String(20), nullable=False)  # train, evaluate, predict
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    train_start_date: Mapped[date | None] = mapped_column(Date)
    train_end_date: Mapped[date | None] = mapped_column(Date)
    eval_start_date: Mapped[date | None] = mapped_column(Date)
    eval_end_date: Mapped[date | None] = mapped_column(Date)
    source_feature_set_ids: Mapped[list | None] = mapped_column(JSON)
    metrics: Mapped[dict | None] = mapped_column(JSON)
    warnings: Mapped[list | None] = mapped_column(JSON)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ModelPrediction(Base):
    __tablename__ = "model_predictions"
    __table_args__ = (
        Index("ix_mp_run_asset", "model_run_id", "asset_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    model_run_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    asset_id: Mapped[str] = mapped_column(String(36), nullable=False)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    as_of: Mapped[date] = mapped_column(Date, nullable=False)
    prediction_horizon_days: Mapped[int] = mapped_column(Integer, default=20)
    prediction_value: Mapped[float | None] = mapped_column(Float)  # predicted return
    prediction_score: Mapped[float | None] = mapped_column(Float)  # normalized -1 to +1
    confidence: Mapped[float | None] = mapped_column(Float)
    quality: Mapped[str] = mapped_column(String(30), default="ok")
    drivers: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ModelValidationReport(Base):
    __tablename__ = "model_validation_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    model_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    horizon_days: Mapped[int] = mapped_column(Integer, default=20)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    directional_accuracy: Mapped[float | None] = mapped_column(Float)
    mean_absolute_error: Mapped[float | None] = mapped_column(Float)
    rank_correlation: Mapped[float | None] = mapped_column(Float)
    hit_rate: Mapped[float | None] = mapped_column(Float)
    avg_confidence: Mapped[float | None] = mapped_column(Float)
    calibration_error: Mapped[float | None] = mapped_column(Float)
    baseline_comparison: Mapped[dict | None] = mapped_column(JSON)
    confidence_buckets: Mapped[dict | None] = mapped_column(JSON)
    promotion_readiness: Mapped[str] = mapped_column(String(30), default="not_ready")
    warnings: Mapped[list | None] = mapped_column(JSON)
