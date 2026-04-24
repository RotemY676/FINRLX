"""Add engine_definitions table and feature_set_id to signal_runs.

Revision ID: 005_engine_reg
Revises: 004_feature
Create Date: 2026-04-24

Domain 4 (Doc 11): Engine registry + signal lineage to feature sets.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005_engine_reg"
down_revision: Union[str, None] = "004_feature"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "engine_definitions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("key", sa.String(80), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("version", sa.String(20), nullable=False, server_default="v1"),
        sa.Column("required_feature_keys", sa.JSON, nullable=True),
        sa.Column("output_kind", sa.String(20), nullable=False, server_default="signal"),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Add feature_set_id to signal_runs for lineage
    with op.batch_alter_table("signal_runs") as batch_op:
        batch_op.add_column(sa.Column("feature_set_id", sa.String(36), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("signal_runs") as batch_op:
        batch_op.drop_column("feature_set_id")
    op.drop_table("engine_definitions")
