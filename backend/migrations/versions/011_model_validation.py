"""Add model_validation_reports table.

Revision ID: 011_model_val
Revises: 010_model_reg
Create Date: 2026-04-25

Phase 6B: ML shadow evaluation and validation reports.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "011_model_val"
down_revision: Union[str, None] = "010_model_reg"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "model_validation_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("model_key", sa.String(80), nullable=False, index=True),
        sa.Column("model_version", sa.String(20), nullable=False, server_default="v1"),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("horizon_days", sa.Integer, server_default=sa.text("20")),
        sa.Column("sample_count", sa.Integer, server_default=sa.text("0")),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("directional_accuracy", sa.Float, nullable=True),
        sa.Column("mean_absolute_error", sa.Float, nullable=True),
        sa.Column("rank_correlation", sa.Float, nullable=True),
        sa.Column("hit_rate", sa.Float, nullable=True),
        sa.Column("avg_confidence", sa.Float, nullable=True),
        sa.Column("calibration_error", sa.Float, nullable=True),
        sa.Column("baseline_comparison", sa.JSON, nullable=True),
        sa.Column("confidence_buckets", sa.JSON, nullable=True),
        sa.Column("promotion_readiness", sa.String(30), server_default="not_ready"),
        sa.Column("warnings", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("model_validation_reports")
