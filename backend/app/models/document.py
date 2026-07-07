"""Phase 17 — Research documents (quarterly filings, annual reports, etc.).

Operators upload PDFs (10-Q, 10-K, transcripts, presentations) against
a ticker. The document is stored on a host-filesystem volume; the
extracted text + metadata lives in this table. Documents are SHARED
BY TICKER per the Phase 17 sharing-model decision — every signed-in
user sees every upload for a given symbol.

The `analyses` model (Phase 17.1) joins back here to capture LLM
question / answer pairs against a specific document.
"""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import gen_uuid

# Extraction lifecycle.  "pending" means the upload finished and the
# extraction task is queued (in Phase 17.0 we extract synchronously, so
# the row goes pending -> ready in one POST; the enum is forward-compat
# for an async worker that may land later).
EXTRACTION_STATUSES = ("pending", "extracting", "ready", "failed")

# Phase 18.3 — origin of the document. "upload" = operator-uploaded PDF
# (storage_path set, external_url null); "sec_auto" = auto-fetched from
# SEC EDGAR (storage_path null, external_url + sec_accession_no set).
# Stored as a free-text VARCHAR rather than a DB enum so adding a new
# source ("news_auto", "earnings_call_auto") later doesn't require an
# enum migration.
DOCUMENT_SOURCES = ("upload", "sec_auto")


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
    # Phase 18.3: NULL for sec_auto rows — those don't have a local
    # file (we persist extracted_text only and point users at SEC for
    # the original via external_url).
    storage_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

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

    # Phase 18.3 — provenance + SEC EDGAR metadata.
    #
    # `source` distinguishes operator uploads from auto-fetched SEC
    # filings. Stored as VARCHAR rather than a DB enum so a future
    # third source (news_auto, transcript_auto) doesn't require a
    # schema migration. Existing rows backfilled to "upload" by the
    # Phase 18.3 migration's server_default.
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="upload"
    )

    # SEC EDGAR's accession number (e.g. "0001045810-26-000012") is
    # globally unique per filing. Used as the dedup key so re-running
    # auto-ingest is idempotent. NULL for operator-uploaded rows
    # (multiple uploads of the same PDF are allowed by design).
    sec_accession_no: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # "10-K" / "10-Q" — denormalized from accession metadata so the FE
    # can render the badge ("Annual Report" / "Quarterly Report")
    # without joining back to an EDGAR cache table. NULL for uploads.
    sec_form: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Reporting period end (e.g. 2026-01-26 = NVIDIA's Q3 FY26). The
    # FE sorts auto-fetched filings by this column so quarters render
    # in calendar order even when filings arrive out-of-order at SEC.
    sec_period_of_report: Mapped[date | None] = mapped_column(Date(), nullable=True)

    # Pointer to the original document at sec.gov. We do NOT cache
    # the HTML locally per the Phase 18 storage decision ("text-only
    # + EDGAR pointer"). The FE uses this for the "Open at SEC" link.
    external_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # Dedup index. Postgres + SQLite both treat NULLs as DISTINCT in
    # composite unique constraints, so multiple uploads (sec_accession_no
    # NULL) coexist while SEC-auto rows are deduped per (ticker,
    # accession_no). The leading `ticker` makes the index useful for the
    # ticker-filtered list query too.
    __table_args__ = (
        Index(
            "uq_research_documents_sec_dedup",
            "ticker",
            "sec_accession_no",
            unique=True,
        ),
    )
