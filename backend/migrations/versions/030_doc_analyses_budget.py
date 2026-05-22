"""Phase 17.1 — DocumentAnalysis + LLMTokenUsage tables.

Pairs the Phase 17.0 ResearchDocument row with the LLM Q&A artifacts
that Phase 17.2 will produce against real Anthropic calls. Both
tables ship empty; the analyze endpoint is the only writer.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# NOTE: Postgres' `alembic_version.version_num` column is VARCHAR(32).
# Revision strings MUST be ≤ 32 characters or the UPDATE at the end of
# the migration raises StringDataRightTruncationError and rolls the
# whole transaction back. The original revision string here was
# "030_document_analyses_and_token_usage" (37 chars) — broke the
# production deploy until this rename landed. Keep new revisions
# concise.
revision: str = "030_doc_analyses_budget"
down_revision: Union[str, None] = "029_research_documents"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_analyses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("created_by_email", sa.String(320), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("model", sa.String(120), nullable=False, server_default=""),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_estimate_usd", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_document_analyses_document_id",
        "document_analyses",
        ["document_id"],
    )
    op.create_index(
        "ix_document_analyses_created_at",
        "document_analyses",
        ["created_at"],
    )

    op.create_table(
        "llm_token_usage",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("input_tokens_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "cost_estimate_usd_total",
            sa.Float(),
            nullable=False,
            server_default="0.0",
        ),
        sa.Column(
            "last_updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "year", "month", "provider", name="uq_llm_token_usage_bucket"
        ),
    )


def downgrade() -> None:
    op.drop_table("llm_token_usage")
    op.drop_index("ix_document_analyses_created_at", "document_analyses")
    op.drop_index("ix_document_analyses_document_id", "document_analyses")
    op.drop_table("document_analyses")
