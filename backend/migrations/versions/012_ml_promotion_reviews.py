"""Add ml_promotion_reviews table.

Revision ID: 012_ml_promo
Revises: 011_model_val
Create Date: 2026-04-25

Phase 6C: ML shadow backtest comparison and promotion governance.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "012_ml_promo"
down_revision: Union[str, None] = "011_model_val"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ml_promotion_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("model_key", sa.String(80), nullable=False, index=True),
        sa.Column("model_version", sa.String(20), nullable=False, server_default="v1"),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("baseline_backtest_id", sa.String(36), nullable=True),
        sa.Column("shadow_backtest_id", sa.String(36), nullable=True),
        sa.Column("validation_report_id", sa.String(36), nullable=True),
        sa.Column("baseline_metrics", sa.JSON, nullable=True),
        sa.Column("shadow_metrics", sa.JSON, nullable=True),
        sa.Column("metric_deltas", sa.JSON, nullable=True),
        sa.Column("sample_count", sa.Integer, server_default=sa.text("0")),
        sa.Column("recommendation", sa.String(30), nullable=False, server_default="not_ready"),
        sa.Column("decision", sa.String(30), nullable=True),
        sa.Column("warnings", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ml_promotion_reviews")
