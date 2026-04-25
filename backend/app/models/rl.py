"""RL environment entities.

Phase 7A: offline-only RL environment foundation.
"""
from datetime import datetime, date

from sqlalchemy import Date, DateTime, Float, Integer, String, Text, JSON, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import gen_uuid


class RLEnvironmentDefinition(Base):
    __tablename__ = "rl_environment_definitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    key: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    universe_id: Mapped[str | None] = mapped_column(String(36))
    state_schema: Mapped[dict | None] = mapped_column(JSON)
    action_schema: Mapped[dict | None] = mapped_column(JSON)
    reward_schema: Mapped[dict | None] = mapped_column(JSON)
    constraint_schema: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    is_shadow_only: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RLEnvironmentRun(Base):
    __tablename__ = "rl_environment_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    environment_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    run_type: Mapped[str] = mapped_column(String(20), nullable=False)
    agent_type: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    universe_id: Mapped[str | None] = mapped_column(String(36))
    policy_snapshot: Mapped[dict | None] = mapped_column(JSON)
    metrics: Mapped[dict | None] = mapped_column(JSON)
    warnings: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RLEpisode(Base):
    __tablename__ = "rl_episodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    environment_run_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    episode_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="completed")
    initial_value: Mapped[float | None] = mapped_column(Float)
    final_value: Mapped[float | None] = mapped_column(Float)
    total_reward: Mapped[float | None] = mapped_column(Float)
    total_return: Mapped[float | None] = mapped_column(Float)
    max_drawdown: Mapped[float | None] = mapped_column(Float)
    turnover: Mapped[float | None] = mapped_column(Float)
    step_count: Mapped[int] = mapped_column(Integer, default=0)
    warnings: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RLStep(Base):
    __tablename__ = "rl_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    episode_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    state: Mapped[dict | None] = mapped_column(JSON)
    action: Mapped[dict | None] = mapped_column(JSON)
    reward: Mapped[float | None] = mapped_column(Float)
    portfolio_value: Mapped[float | None] = mapped_column(Float)
    cash_weight: Mapped[float | None] = mapped_column(Float)
    exposure: Mapped[float | None] = mapped_column(Float)
    constraint_violations: Mapped[list | None] = mapped_column(JSON)
    metadata_: Mapped[dict | None] = mapped_column("metadata_", JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
