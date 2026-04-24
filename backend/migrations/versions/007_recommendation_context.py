"""Add context field to recommendations for live/backtest isolation.

Revision ID: 007_rec_context
Revises: 006_rec_lineage
Create Date: 2026-04-24

Phase 5A+B.1: backtest recommendations must not pollute live current view.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007_rec_context"
down_revision: Union[str, None] = "006_rec_lineage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("recommendations") as batch_op:
        batch_op.add_column(sa.Column("context", sa.String(20), server_default="live"))


def downgrade() -> None:
    with op.batch_alter_table("recommendations") as batch_op:
        batch_op.drop_column("context")
