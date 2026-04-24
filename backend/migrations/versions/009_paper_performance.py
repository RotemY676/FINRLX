"""Add paper valuation snapshots and trade ledger tables.

Revision ID: 009_paper_perf
Revises: 008_paper_prov
Create Date: 2026-04-25

Phase 5D: time-series performance + trade ledger for paper portfolios.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "009_paper_perf"
down_revision: Union[str, None] = "008_paper_prov"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "paper_valuation_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("portfolio_id", sa.String(36), nullable=False, index=True),
        sa.Column("valuation_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("portfolio_value", sa.Float, server_default=sa.text("0.0")),
        sa.Column("cash_value", sa.Float, server_default=sa.text("0.0")),
        sa.Column("invested_value", sa.Float, server_default=sa.text("0.0")),
        sa.Column("daily_return", sa.Float, nullable=True),
        sa.Column("cumulative_return", sa.Float, nullable=True),
        sa.Column("max_drawdown_to_date", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "paper_trades",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("portfolio_id", sa.String(36), nullable=False, index=True),
        sa.Column("recommendation_id", sa.String(36), nullable=True),
        sa.Column("trade_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("asset_id", sa.String(36), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("side", sa.String(10), nullable=False),
        sa.Column("quantity", sa.Integer, server_default=sa.text("0")),
        sa.Column("price", sa.Float, server_default=sa.text("0.0")),
        sa.Column("notional", sa.Float, server_default=sa.text("0.0")),
        sa.Column("weight_delta", sa.Float, nullable=True),
        sa.Column("reason", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("paper_trades")
    op.drop_table("paper_valuation_snapshots")
