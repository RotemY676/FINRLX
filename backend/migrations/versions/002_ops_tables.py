"""Add ops tables: data_feeds, policy_breaches, publication_queue.

Revision ID: 002_ops_tables
Revises: 001_initial
Create Date: 2026-04-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_ops_tables"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "data_feeds",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(30), server_default="ok"),
        sa.Column("lag", sa.String(30), server_default="0s"),
        sa.Column("coverage", sa.String(20), server_default="100%"),
        sa.Column("slo", sa.Float, server_default=sa.text("1.0")),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "policy_breaches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("kind", sa.String(50), nullable=False),
        sa.Column("label", sa.String(300), nullable=False),
        sa.Column("utilization", sa.Float, nullable=False),
        sa.Column("trend", sa.String(30), server_default="+0%"),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("related", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "publication_queue",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("recommendation_id", sa.String(50), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("stance", sa.String(20), nullable=False),
        sa.Column("version", sa.String(10), server_default="v1"),
        sa.Column("submitter", sa.String(100), nullable=False),
        sa.Column("weight", sa.String(30), server_default="0%"),
        sa.Column("confidence", sa.Float, server_default=sa.text("0.5")),
        sa.Column("flags", sa.JSON, nullable=True),
        sa.Column("priority", sa.String(10), server_default="mid"),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("submitted_ago", sa.String(30), server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("publication_queue")
    op.drop_table("policy_breaches")
    op.drop_table("data_feeds")
