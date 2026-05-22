"""Phase 17.0 — Research documents table.

Stores PDFs uploaded against a ticker (10-Q, 10-K, transcripts) plus
the extracted text. Shared by ticker — no per-user partitioning.
Analyses (Phase 17.1) will reference these rows by `document_id`.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "029_research_documents"
down_revision: Union[str, None] = "028_operator_analyses"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "research_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        # Always uppercase. Index drives the ticker-listing query.
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        # Relative to settings.documents_storage_path. Conventional layout:
        # "<TICKER>/<uuid>.pdf"
        sa.Column("storage_path", sa.String(512), nullable=False),
        sa.Column(
            "mime_type",
            sa.String(80),
            nullable=False,
            server_default="application/pdf",
        ),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("extracted_text_tokens_estimate", sa.Integer(), nullable=True),
        sa.Column(
            "extraction_status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("extraction_error", sa.Text(), nullable=True),
        # Operator email is for audit / "uploaded by" labelling only —
        # the sharing model is "shared by ticker", not "private per
        # uploader".
        sa.Column("uploaded_by_email", sa.String(320), nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_research_documents_ticker",
        "research_documents",
        ["ticker"],
    )
    op.create_index(
        "ix_research_documents_uploaded_at",
        "research_documents",
        ["uploaded_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_research_documents_uploaded_at", "research_documents")
    op.drop_index("ix_research_documents_ticker", "research_documents")
    op.drop_table("research_documents")
