"""Validation, backtest, and paper portfolio entities.

Maps to Data Model doc 11, Domain 7: Validation, Backtest, Paper, Replay.
"""
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, func
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
    # MVP-1: tenant column (nullable; enforced in MVP-4)
    user_id: Mapped[str | None] = mapped_column(String(36), index=True)

    current_holdings: Mapped[dict | None] = mapped_column(JSON)
    cash_weight: Mapped[float] = mapped_column(Float, default=1.0)
    portfolio_value: Mapped[float] = mapped_column(Float, default=100000.0)
    last_rebalance_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_rebalances: Mapped[int] = mapped_column(Integer, default=0)

    # Provenance (Phase 5C)
    source_recommendation_id: Mapped[str | None] = mapped_column(String(36))
    source_type: Mapped[str] = mapped_column(String(30), default="unknown")  # recommendation_paper, seed_demo, unknown
    events_log: Mapped[list | None] = mapped_column(JSON)


class PaperValuationSnapshot(Base):
    __tablename__ = "paper_valuation_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    portfolio_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    valuation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    portfolio_value: Mapped[float] = mapped_column(Float, default=0.0)
    cash_value: Mapped[float] = mapped_column(Float, default=0.0)
    invested_value: Mapped[float] = mapped_column(Float, default=0.0)
    daily_return: Mapped[float | None] = mapped_column(Float)
    cumulative_return: Mapped[float | None] = mapped_column(Float)
    max_drawdown_to_date: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PaperTrade(Base):
    __tablename__ = "paper_trades"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    portfolio_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    recommendation_id: Mapped[str | None] = mapped_column(String(36))
    trade_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    asset_id: Mapped[str] = mapped_column(String(36), nullable=False)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # buy, sell
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    notional: Mapped[float] = mapped_column(Float, default=0.0)
    weight_delta: Mapped[float | None] = mapped_column(Float)
    reason: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ReplaySnapshot(Base, TimestampMixin):
    __tablename__ = "replay_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    recommendation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    stage: Mapped[str] = mapped_column(String(50), nullable=False)  # selection, allocation, timing, risk, publication
    snapshot_data: Mapped[dict | None] = mapped_column(JSON)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
