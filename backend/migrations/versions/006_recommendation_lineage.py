"""Add pipeline lineage fields to recommendations.

Revision ID: 006_rec_lineage
Revises: 005_engine_reg
Create Date: 2026-04-24

Phase 4D: source_feature_set_id and source_signal_run_ids for traceability.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006_rec_lineage"
down_revision: Union[str, None] = "005_engine_reg"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("recommendations") as batch_op:
        batch_op.add_column(sa.Column("source_feature_set_id", sa.String(36), nullable=True))
        batch_op.add_column(sa.Column("source_signal_run_ids", sa.JSON, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("recommendations") as batch_op:
        batch_op.drop_column("source_signal_run_ids")
        batch_op.drop_column("source_feature_set_id")
