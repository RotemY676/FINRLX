"""Add feature tables: feature_definitions, feature_sets, feature_values.

Revision ID: 004_feature
Revises: 003_ingestion
Create Date: 2026-04-24

Domain 3 (Doc 11): Feature Registry.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004_feature"
down_revision: Union[str, None] = "003_ingestion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feature_definitions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("key", sa.String(80), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("version", sa.String(20), nullable=False, server_default="v1"),
        sa.Column("lookback_days", sa.Integer, nullable=False, server_default=sa.text("20")),
        sa.Column("input_kind", sa.String(20), nullable=False, server_default="bars"),
        sa.Column("output_type", sa.String(20), nullable=False, server_default="float"),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "feature_sets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("universe_id", sa.String(36), nullable=True),
        sa.Column("as_of", sa.Date, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("feature_version", sa.String(20), nullable=False, server_default="v1"),
        sa.Column("source_manifest_ids", sa.JSON, nullable=True),
        sa.Column("asset_count", sa.Integer, server_default=sa.text("0")),
        sa.Column("feature_count", sa.Integer, server_default=sa.text("0")),
        sa.Column("completeness_score", sa.Float, server_default=sa.text("0.0")),
        sa.Column("freshness_status", sa.String(20), server_default="unknown"),
        sa.Column("warnings", sa.JSON, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_feature_set_as_of", "feature_sets", ["as_of"])

    op.create_table(
        "feature_values",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("feature_set_id", sa.String(36), nullable=False, index=True),
        sa.Column("asset_id", sa.String(36), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("feature_key", sa.String(80), nullable=False),
        sa.Column("value", sa.Float, nullable=True),
        sa.Column("unit", sa.String(20), nullable=True),
        sa.Column("window_days", sa.Integer, nullable=True),
        sa.Column("quality", sa.String(30), nullable=False, server_default="ok"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_fv_set_asset", "feature_values", ["feature_set_id", "asset_id"])
    op.create_index("ix_fv_set_key", "feature_values", ["feature_set_id", "feature_key"])


def downgrade() -> None:
    op.drop_table("feature_values")
    op.drop_table("feature_sets")
    op.drop_table("feature_definitions")
