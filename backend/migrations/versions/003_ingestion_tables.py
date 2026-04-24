"""Add ingestion tables: market_bars, news_events, ingestion_manifests.

Revision ID: 003_ingestion
Revises: 002_ops_tables
Create Date: 2026-04-24

Domain 2 (Doc 11): Raw and Curated Inputs.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003_ingestion"
down_revision: Union[str, None] = "002_ops_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "market_bars",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("asset_id", sa.String(36), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False, index=True),
        sa.Column("bar_date", sa.Date, nullable=False),
        sa.Column("interval", sa.String(10), nullable=False, server_default="1d"),
        sa.Column("open", sa.Float, nullable=False),
        sa.Column("high", sa.Float, nullable=False),
        sa.Column("low", sa.Float, nullable=False),
        sa.Column("close", sa.Float, nullable=False),
        sa.Column("volume", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("source", sa.String(50), nullable=False, server_default="local"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("asset_id", "bar_date", "interval", name="uq_market_bar"),
    )
    op.create_index("ix_market_bar_asset_date", "market_bars", ["asset_id", "bar_date"])

    op.create_table(
        "news_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("headline", sa.String(500), nullable=False),
        sa.Column("body", sa.Text, nullable=True),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("url", sa.String(500), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tickers", sa.JSON, nullable=True),
        sa.Column("sentiment_score", sa.Float, nullable=True),
        sa.Column("sentiment_label", sa.String(20), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_news_event_published", "news_events", ["published_at"])

    op.create_table(
        "ingestion_manifests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("asset_count", sa.Integer, server_default=sa.text("0")),
        sa.Column("row_count", sa.Integer, server_default=sa.text("0")),
        sa.Column("date_from", sa.Date, nullable=True),
        sa.Column("date_to", sa.Date, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("details", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_manifest_source", "ingestion_manifests", ["source"])


def downgrade() -> None:
    op.drop_table("ingestion_manifests")
    op.drop_table("news_events")
    op.drop_table("market_bars")
