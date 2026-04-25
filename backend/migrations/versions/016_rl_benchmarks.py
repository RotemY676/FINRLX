"""Add rl_benchmark_reports table.

Revision ID: 016_rl_bench
Revises: 015_rl_train
Create Date: 2026-04-25

Phase 7C: offline RL benchmarking and forensic comparison.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "016_rl_bench"
down_revision: Union[str, None] = "015_rl_train"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rl_benchmark_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("environment_key", sa.String(80), nullable=False),
        sa.Column("universe_id", sa.String(36), nullable=True),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("compared_agents", sa.JSON, nullable=True),
        sa.Column("metrics_by_agent", sa.JSON, nullable=True),
        sa.Column("reward_breakdown_by_agent", sa.JSON, nullable=True),
        sa.Column("violations_by_agent", sa.JSON, nullable=True),
        sa.Column("forensic_summary", sa.JSON, nullable=True),
        sa.Column("simulation_run_ids", sa.JSON, nullable=True),
        sa.Column("policy_snapshot_ids", sa.JSON, nullable=True),
        sa.Column("dataset_lineage", sa.JSON, nullable=True),
        sa.Column("safety_flags", sa.JSON, nullable=True),
        sa.Column("warnings", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("rl_benchmark_reports")
