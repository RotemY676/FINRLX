"""Add ML model registry tables.

Revision ID: 010_model_reg
Revises: 009_paper_perf
Create Date: 2026-04-25

Phase 6A: model_definitions, model_runs, model_predictions.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "010_model_reg"
down_revision: Union[str, None] = "009_paper_perf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "model_definitions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("key", sa.String(80), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("model_type", sa.String(50), nullable=False, server_default="baseline_linear"),
        sa.Column("target", sa.String(100), nullable=False, server_default="forward_return_20d"),
        sa.Column("feature_keys", sa.JSON, nullable=True),
        sa.Column("prediction_horizon_days", sa.Integer, server_default=sa.text("20")),
        sa.Column("version", sa.String(20), nullable=False, server_default="v1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="experimental"),
        sa.Column("is_shadow", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "model_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("model_key", sa.String(80), nullable=False, index=True),
        sa.Column("model_version", sa.String(20), nullable=False, server_default="v1"),
        sa.Column("run_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("train_start_date", sa.Date, nullable=True),
        sa.Column("train_end_date", sa.Date, nullable=True),
        sa.Column("eval_start_date", sa.Date, nullable=True),
        sa.Column("eval_end_date", sa.Date, nullable=True),
        sa.Column("source_feature_set_ids", sa.JSON, nullable=True),
        sa.Column("metrics", sa.JSON, nullable=True),
        sa.Column("warnings", sa.JSON, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "model_predictions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("model_run_id", sa.String(36), nullable=False, index=True),
        sa.Column("asset_id", sa.String(36), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("as_of", sa.Date, nullable=False),
        sa.Column("prediction_horizon_days", sa.Integer, server_default=sa.text("20")),
        sa.Column("prediction_value", sa.Float, nullable=True),
        sa.Column("prediction_score", sa.Float, nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("quality", sa.String(30), server_default="ok"),
        sa.Column("drivers", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_mp_run_asset", "model_predictions", ["model_run_id", "asset_id"])


def downgrade() -> None:
    op.drop_table("model_predictions")
    op.drop_table("model_runs")
    op.drop_table("model_definitions")
