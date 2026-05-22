"""Phase 17 — Research documents (quarterly filings, annual reports, etc.).

Operators upload PDFs (10-Q, 10-K, transcripts, presentations) against
a ticker. The document is stored on a host-filesystem volume; the
extracted text + metadata lives in this table. Documents are SHARED
BY TICKER per the Phase 17 sharing-model decision — every signed-in
user sees every upload for a given symbol.

The `analyses` model (Phase 17.1) joins back here to capture LLM
question / answer pairs against a specific document.
"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import gen_uuid


# Extraction lifecycle.  "pending" means the upload finished and the
# extraction task is queued (in Phase 17.0 we extract synchronously, so
# the row goes pending -> ready in one POST; the enum is forward-compat
# for an async worker that may land later).
EXTRACTION_STATUSES = ("pending", "extracting", "ready", "failed")


class ResearchDocument(Base):
    __tablename__ = "research_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)

    # SHARED-BY-TICKER lookup key. Always upper-cased on insert so the
    # B-tree index sees the canonical form. Ticker validation lives at
    # the API layer (mirrors the Phase 16 regex).
    ticker: Mapped[str] = mapped_column(String(16), nullable=False, index=True)

    # Original filename as the user uploaded it. Useful for the FE to
    # show a recognisable name; not used for storage routing.
    filename: Mapped[str] = mapped_column(String(255), nullable=False)

    # Path RELATIVE to `settings.documents_storage_path`. The storage
    # layer chooses the layout (`<ticker>/<uuid>.pdf`). Storing relative
    # paths means we can move the volume mount without rewriting rows.
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)

    mime_type: Mapped[str] = mapped_column(String(80), nullable=False, default="application/pdf")
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Extracted text — can be large (50K+ chars for a 10-Q). Stored in
    # DB for now; if the corpus grows we may move to a content-
    # addressed blob alongside the PDF.
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Approximate token count (chars // 4) — used by the Phase 17.1
    # token budget tracker to estimate the cost of analysing this
    # document before the LLM call.
    extracted_text_tokens_estimate: Mapped[int | None] = mapped_column(Integer, nullable=True)

    extraction_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    extraction_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Operator who performed the upload. Documents are shared by ticker
    # so the email is for audit / "uploaded by" labelling, not access
    # control. Owner-or-admin can delete; anyone signed-in can read.
    uploaded_by_email: Mapped[str] = mapped_column(String(320), nullable=False)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
