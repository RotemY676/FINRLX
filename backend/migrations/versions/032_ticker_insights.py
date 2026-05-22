"""Phase 18.5 — ticker_insights table.

Cross-document LLM-generated insights (trajectory + latest-quarter
delta across a ticker's recent filings). One row per generation
event; the FE shows the most recent and offers regeneration when it
ages past 7 days.

Separate table from `document_analyses` because insights are a
CROSS-document artifact, not tied to a single ResearchDocument row.

Revision string: 24 chars, well under the alembic 32-char cap.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "032_ticker_insights"
down_revision: Union[str, None] = "031_research_doc_sec_source"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ticker_insights",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=False),
        # JSON works on both Postgres (native) and SQLite (TEXT under the
        # hood). The Python-side type is list[str] (accession numbers).
        sa.Column("quarters_covered", sa.JSON(), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("model", sa.String(120), nullable=False, server_default=""),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_estimate_usd", sa.Float(), nullable=True),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("generated_by_email", sa.String(320), nullable=False),
    )
    # Composite index for the dominant query ("most recent for ticker").
    # The leading column drives the WHERE filter; the second supports
    # the ORDER BY generated_at DESC LIMIT 1 pattern.
    op.create_index(
        "ix_ticker_insights_ticker_generated_at",
        "ticker_insights",
        ["ticker", "generated_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_ticker_insights_ticker_generated_at", "ticker_insights")
    op.drop_table("ticker_insights")
