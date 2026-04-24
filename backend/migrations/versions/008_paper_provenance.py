"""Add provenance fields to paper_portfolios.

Revision ID: 008_paper_prov
Revises: 007_rec_context
Create Date: 2026-04-24

Phase 5C: source_recommendation_id, source_type, portfolio_value, events_log.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "008_paper_prov"
down_revision: Union[str, None] = "007_rec_context"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("paper_portfolios") as batch_op:
        batch_op.add_column(sa.Column("portfolio_value", sa.Float, server_default=sa.text("100000.0")))
        batch_op.add_column(sa.Column("source_recommendation_id", sa.String(36), nullable=True))
        batch_op.add_column(sa.Column("source_type", sa.String(30), server_default="unknown"))
        batch_op.add_column(sa.Column("events_log", sa.JSON, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("paper_portfolios") as batch_op:
        batch_op.drop_column("events_log")
        batch_op.drop_column("source_type")
        batch_op.drop_column("source_recommendation_id")
        batch_op.drop_column("portfolio_value")
