"""Validation, backtest, and paper portfolio entities.

Maps to Data Model doc 11, Domain 7: Validation, Backtest, Paper, Replay.
"""
from datetime import datetime

from sqlalchemy import DateTime, String, Text, Float, JSON, Boolean, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, gen_uuid


class BacktestExperiment(Base, TimestampMixin):
    __tablename__ = "backtest_experiments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending, running, completed, failed
    policy_version_id: Mapped[str | None] = mapped_column(String(36))
    universe_id: Mapped[str | None] = mapped_column(String(36))

    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    config: Mapped[dict | None] = mapped_column(JSON)
    results_summary: Mapped[dict | None] = mapped_column(JSON)
    is_promoted: Mapped[bool] = mapped_column(Boolean, default=False)


class PaperPortfolio(Base, TimestampMixin):
    __tablename__ = "paper_portfolios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    current_holdings: Mapped[dict | None] = mapped_column(JSON)  # {asset_id: weight}
    cash_weight: Mapped[float] = mapped_column(Float, default=1.0)
    last_rebalance_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_rebalances: Mapped[int] = mapped_column(Integer, default=0)


class ReplaySnapshot(Base, TimestampMixin):
    __tablename__ = "replay_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    recommendation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    stage: Mapped[str] = mapped_column(String(50), nullable=False)  # selection, allocation, timing, risk, publication
    snapshot_data: Mapped[dict | None] = mapped_column(JSON)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
