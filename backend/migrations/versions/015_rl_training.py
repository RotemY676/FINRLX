"""Add RL agent registry and training tables.

Revision ID: 015_rl_train
Revises: 014_rl_env
Create Date: 2026-04-25

Phase 7B: offline RL training harness.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "015_rl_train"
down_revision: Union[str, None] = "014_rl_env"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rl_agent_definitions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("key", sa.String(80), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("agent_type", sa.String(50), nullable=False),
        sa.Column("algorithm_family", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="baseline"),
        sa.Column("is_trainable", sa.Boolean, server_default=sa.text("false")),
        sa.Column("is_shadow_only", sa.Boolean, server_default=sa.text("true")),
        sa.Column("config_schema", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "rl_training_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("agent_key", sa.String(80), nullable=False, index=True),
        sa.Column("environment_key", sa.String(80), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("train_start_date", sa.Date, nullable=True),
        sa.Column("train_end_date", sa.Date, nullable=True),
        sa.Column("eval_start_date", sa.Date, nullable=True),
        sa.Column("eval_end_date", sa.Date, nullable=True),
        sa.Column("config", sa.JSON, nullable=True),
        sa.Column("metrics", sa.JSON, nullable=True),
        sa.Column("warnings", sa.JSON, nullable=True),
        sa.Column("model_artifact_ref", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "rl_policy_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("training_run_id", sa.String(36), nullable=True, index=True),
        sa.Column("agent_key", sa.String(80), nullable=False, index=True),
        sa.Column("environment_key", sa.String(80), nullable=False),
        sa.Column("policy_type", sa.String(50), nullable=False),
        sa.Column("policy_payload", sa.JSON, nullable=True),
        sa.Column("metrics", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("rl_policy_snapshots")
    op.drop_table("rl_training_runs")
    op.drop_table("rl_agent_definitions")
