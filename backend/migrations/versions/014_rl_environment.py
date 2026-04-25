"""Add RL environment tables.

Revision ID: 014_rl_env
Revises: 013_policy_rules
Create Date: 2026-04-25

Phase 7A: offline-only RL environment foundation.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "014_rl_env"
down_revision: Union[str, None] = "013_policy_rules"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rl_environment_definitions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("key", sa.String(80), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("universe_id", sa.String(36), nullable=True),
        sa.Column("state_schema", sa.JSON, nullable=True),
        sa.Column("action_schema", sa.JSON, nullable=True),
        sa.Column("reward_schema", sa.JSON, nullable=True),
        sa.Column("constraint_schema", sa.JSON, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("is_shadow_only", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "rl_environment_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("environment_key", sa.String(80), nullable=False, index=True),
        sa.Column("run_type", sa.String(20), nullable=False),
        sa.Column("agent_type", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("universe_id", sa.String(36), nullable=True),
        sa.Column("policy_snapshot", sa.JSON, nullable=True),
        sa.Column("metrics", sa.JSON, nullable=True),
        sa.Column("warnings", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "rl_episodes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("environment_run_id", sa.String(36), nullable=False, index=True),
        sa.Column("episode_index", sa.Integer, nullable=False),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("status", sa.String(20), server_default="completed"),
        sa.Column("initial_value", sa.Float, nullable=True),
        sa.Column("final_value", sa.Float, nullable=True),
        sa.Column("total_reward", sa.Float, nullable=True),
        sa.Column("total_return", sa.Float, nullable=True),
        sa.Column("max_drawdown", sa.Float, nullable=True),
        sa.Column("turnover", sa.Float, nullable=True),
        sa.Column("step_count", sa.Integer, server_default=sa.text("0")),
        sa.Column("warnings", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "rl_steps",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("episode_id", sa.String(36), nullable=False, index=True),
        sa.Column("step_index", sa.Integer, nullable=False),
        sa.Column("as_of_date", sa.Date, nullable=False),
        sa.Column("state", sa.JSON, nullable=True),
        sa.Column("action", sa.JSON, nullable=True),
        sa.Column("reward", sa.Float, nullable=True),
        sa.Column("portfolio_value", sa.Float, nullable=True),
        sa.Column("cash_weight", sa.Float, nullable=True),
        sa.Column("exposure", sa.Float, nullable=True),
        sa.Column("constraint_violations", sa.JSON, nullable=True),
        sa.Column("metadata_", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("rl_steps")
    op.drop_table("rl_episodes")
    op.drop_table("rl_environment_runs")
    op.drop_table("rl_environment_definitions")
