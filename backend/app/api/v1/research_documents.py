"""Phase 17.0 — Research documents API.

Operators upload quarterly / annual filings (PDFs) against a ticker.
The extracted text + metadata is stored in `research_documents` and
made available for Phase 17.1's analyze endpoint.

Sharing model: SHARED BY TICKER. Every signed-in user sees every
upload for a given symbol. Upload + delete require auth; read/list
require auth (we keep this surface auth-gated even though documents
are shared, because the corpus may contain proprietary text the
operator pasted in).

Endpoints:
  - POST   /api/v1/research/documents          multipart upload
  - GET    /api/v1/research/documents?ticker=  list by ticker
  - GET    /api/v1/research/documents/{id}     single document metadata
  - GET    /api/v1/research/documents/{id}/download   raw PDF bytes
  - DELETE /api/v1/research/documents/{id}     soft-cap to uploader/admin

Ticker validation mirrors Phase 16 (A-Z{1..8} with optional sub-suffix)
so a single regex governs what's accepted across the research surface.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from fastapi import File as FastAPIFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_deps import get_current_user
from app.api.deps import make_meta
from app.core.config import settings
from app.core.database import get_db
from app.models.auth import User
from app.models.document import ResearchDocument
from app.schemas.common import ApiResponse
from app.services.documents import (
    DocumentExtractionError,
    DocumentStorageError,
    delete_document,
    estimate_tokens,
    extract_text_from_pdf,
    open_document,
    save_document,
)


router = APIRouter()

# Mirrors the Phase 16 regex so the regex used to validate a ticker on
# /research/[ticker] also validates upload tickers — same canonical form.
_TICKER_RE = re.compile(r"^[A-Z]{1,8}(\.[A-Z]{1,4})?$")

_ACCEPTED_MIME_TYPES = frozenset(
    {
        "application/pdf",
        # Some browsers send the generic octet-stream for .pdf uploads;
        # we accept and rely on pypdf to reject non-PDF bytes downstream.
        "application/octet-stream",
    }
)


# ── Schemas ────────────────────────────────────────────────────────────


class DocumentSummary(BaseModel):
    """Lightweight document row for the list endpoint — no extracted text."""

    id: str
    ticker: str
    filename: str
    mime_type: str
    file_size_bytes: int
    extracted_text_tokens_estimate: Optional[int] = None
    extraction_status: str
    extraction_error: Optional[str] = None
    uploaded_by_email: str
    uploaded_at: datetime


class DocumentDetail(DocumentSummary):
    """Full document row, including the extracted text body."""

    extracted_text: Optional[str] = None


class DocumentListResponse(BaseModel):
    ticker: str
    documents: list[DocumentSummary] = Field(default_factory=list)
    total: int


# ── Helpers ────────────────────────────────────────────────────────────


def _validate_ticker(raw: str) -> str:
    upper = raw.strip().upper()
    if not _TICKER_RE.match(upper):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid ticker symbol. Must match [A-Z]{1,8} with an optional "
                ".[A-Z]{1,4} suffix (e.g. NVDA, MSFT, BRK.B)."
            ),
        )
    return upper


def _row_to_summary(row: ResearchDocument) -> DocumentSummary:
    return DocumentSummary(
        id=row.id,
        ticker=row.ticker,
        filename=row.filename,
        mime_type=row.mime_type,
        file_size_bytes=row.file_size_bytes,
        extracted_text_tokens_estimate=row.extracted_text_tokens_estimate,
        extraction_status=row.extraction_status,
        extraction_error=row.extraction_error,
        uploaded_by_email=row.uploaded_by_email,
        uploaded_at=row.uploaded_at,
    )


def _row_to_detail(row: ResearchDocument) -> DocumentDetail:
    return DocumentDetail(
        **_row_to_summary(row).model_dump(),
        extracted_text=row.extracted_text,
    )


# ── Endpoints ──────────────────────────────────────────────────────────


@router.post(
    "/research/documents",
    response_model=ApiResponse[DocumentDetail],
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    ticker: str = Form(...),
    file: UploadFile = FastAPIFile(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DocumentDetail]:
    """Upload a PDF against a ticker. Text extraction runs synchronously
    inside the request — typical 10-Q filings extract in well under a
    second. The row is committed only after extraction succeeds; on
    extraction failure the row is committed with status="failed" so the
    UI can show the error and the operator can re-upload."""
    symbol = _validate_ticker(ticker)

    # Pre-read content-type sanity check. We still rely on pypdf to
    # confirm the bytes are a real PDF; the content-type is a courtesy
    # short-circuit.
    if file.content_type and file.content_type not in _ACCEPTED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Expected application/pdf, received {file.content_type}.",
        )

    content = await file.read()
    max_bytes = settings.documents_max_size_mb * 1024 * 1024
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File exceeds the {settings.documents_max_size_mb} MB upload limit. "
                f"Received {len(content) // (1024 * 1024)} MB."
            ),
        )

    # Persist the bytes first so we have the file on disk before any
    # DB row references it. If extraction fails we still keep the bytes
    # for re-attempt and surface the failure on the row.
    try:
        relative_path, size_bytes = save_document(symbol, content, suffix=".pdf")
    except DocumentStorageError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage write failed: {e}",
        ) from e

    extracted_text: str | None = None
    tokens_estimate: int | None = None
    extraction_status = "ready"
    extraction_error: str | None = None
    try:
        extracted_text = extract_text_from_pdf(content)
        tokens_estimate = estimate_tokens(extracted_text)
    except DocumentExtractionError as e:
        extraction_status = "failed"
        extraction_error = str(e)

    row = ResearchDocument(
        ticker=symbol,
        filename=file.filename or "document.pdf",
        storage_path=relative_path,
        mime_type=file.content_type or "application/pdf",
        file_size_bytes=size_bytes,
        extracted_text=extracted_text,
        extracted_text_tokens_estimate=tokens_estimate,
        extraction_status=extraction_status,
        extraction_error=extraction_error,
        uploaded_by_email=user.email,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    return ApiResponse(meta=make_meta(), data=_row_to_detail(row))


@router.get(
    "/research/documents",
    response_model=ApiResponse[DocumentListResponse],
)
async def list_documents(
    ticker: str = Query(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DocumentListResponse]:
    """List documents shared by a ticker. Most-recent first."""
    _ = user  # auth gate; no per-user filtering (shared-by-ticker model).
    symbol = _validate_ticker(ticker)
    result = await db.execute(
        select(ResearchDocument)
        .where(ResearchDocument.ticker == symbol)
        .order_by(ResearchDocument.uploaded_at.desc())
    )
    rows = result.scalars().all()
    summaries = [_row_to_summary(r) for r in rows]
    return ApiResponse(
        meta=make_meta(),
        data=DocumentListResponse(ticker=symbol, documents=summaries, total=len(summaries)),
    )


@router.get(
    "/research/documents/{document_id}",
    response_model=ApiResponse[DocumentDetail],
)
async def get_document(
    document_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DocumentDetail]:
    """Return the full document row, including the extracted text body."""
    _ = user  # auth gate.
    row = await db.get(ResearchDocument, document_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )
    return ApiResponse(meta=make_meta(), data=_row_to_detail(row))


@router.get("/research/documents/{document_id}/download")
async def download_document(
    document_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Stream the original PDF bytes. The `Content-Disposition` is
    `attachment` so browsers download rather than render inline (FINRLX
    is not a PDF viewer)."""
    _ = user
    row = await db.get(ResearchDocument, document_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )
    try:
        content = open_document(row.storage_path)
    except DocumentStorageError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document bytes are missing on disk: {e}",
        ) from e
    return Response(
        content=content,
        media_type=row.mime_type or "application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{row.filename}"',
        },
    )


@router.delete(
    "/research/documents/{document_id}",
    response_model=ApiResponse[dict],
)
async def remove_document(
    document_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    """Delete a document. Only the uploader can delete in Phase 17.0;
    an admin role gate lands when we have a real role model. The on-disk
    bytes are removed best-effort; the DB row is the source of truth for
    "does this document exist."
    """
    row = await db.get(ResearchDocument, document_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )
    if row.uploaded_by_email.lower() != user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the uploader can delete this document.",
        )
    # Best-effort: filesystem deletion never blocks the DB row deletion.
    try:
        delete_document(row.storage_path)
    except DocumentStorageError:
        pass
    await db.delete(row)
    await db.commit()
    return ApiResponse(meta=make_meta(), data={"id": document_id, "deleted": True})
