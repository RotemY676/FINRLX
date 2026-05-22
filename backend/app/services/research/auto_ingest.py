"""Phase 18.4 — Auto-ingest orchestrator.

Composes the single-purpose EDGAR services (resolve, list, download,
extract) into the flow the auto-ingest endpoint invokes:

    resolve_ticker → fetch_recent_quarterly_filings → for each:
       dedup-check → fetch_filing_bytes → extract → persist

Design choices:

- **Per-filing commit, not all-or-nothing.** If filing #3 fails to
  download, we still commit #1, #2, #4, #5, #6 — partial results are
  more useful than nothing, and the next auto-ingest run will pick up
  whatever failed via dedup (the un-ingested accessions stay
  unrecorded so the next pass retries them).

- **Dedup by `(ticker, sec_accession_no)`** matches the unique index
  added in 18.3's migration 031. We check before downloading so we
  don't waste SEC rate-limit budget on a filing we already have.

- **uploaded_by_email holds the triggering user's email.** Documents
  are shared by ticker per the Phase 17 sharing model, so the email
  is for audit only. The user who triggered the auto-ingest gets
  recorded as the "uploader" so the existing delete-permission logic
  (owner-or-admin) still applies if they later want to remove the
  auto-fetched row.

- **Sequential downloads, not concurrent.** SEC enforces ≤10
  requests/sec, and a sustained burst from a single IP can trip
  abuse heuristics. 6 sequential downloads cost ~10–30s wall time;
  acceptable for a foreground request.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import ResearchDocument
from app.services.documents.extraction import estimate_tokens
from app.services.edgar import (
    EdgarConfigError,
    EdgarExtractionError,
    EdgarUpstreamError,
    extract_text_from_filing,
    fetch_filing_bytes,
    fetch_recent_quarterly_filings,
    resolve_ticker,
)

logger = logging.getLogger(__name__)


class TickerNotCoveredError(RuntimeError):
    """Raised when SEC's table has no entry for the requested ticker —
    typically a non-US listing. Distinct from upstream errors because
    the caller's translation is "404 user-fixable" not "503 transient"."""


@dataclass
class AutoIngestFailure:
    """A single filing that couldn't be ingested. Surfaced in the
    endpoint response so the operator can investigate which accessions
    have problems without trawling Railway logs."""
    accession_no: str
    form: str
    reason: str


@dataclass
class AutoIngestResult:
    ticker: str
    cik: str
    ingested: int                                     # newly persisted
    skipped_existing: int                             # dedup hits
    failed: int                                       # download/extract failures
    failures: list[AutoIngestFailure] = field(default_factory=list)
    document_ids: list[str] = field(default_factory=list)  # full set: new + existing


async def auto_ingest_filings(
    db: AsyncSession,
    *,
    ticker: str,
    triggered_by_email: str,
    limit: int = 6,
) -> AutoIngestResult:
    """Walk the EDGAR pipeline for a single ticker, persisting any
    quarterly filings not already in the database.

    Args:
      db: open async session. The orchestrator commits per-filing so
        the caller does NOT need to (and should not) commit again.
      ticker: stock symbol. Case-insensitive; uppercased on the way in.
      triggered_by_email: recorded on each new ResearchDocument row.
      limit: max number of filings to consider (default 6 ≈ 18 months).

    Raises:
      - TickerNotCoveredError: ticker not in SEC's table (caller →404).
      - EdgarConfigError: SEC_USER_AGENT misconfigured (caller →503).
      - EdgarUpstreamError: SEC's submissions endpoint unreachable
        (caller →503). Individual filing-download failures do NOT
        raise — they're tallied into result.failures.
    """
    symbol = ticker.strip().upper()

    cik = await resolve_ticker(symbol)
    if cik is None:
        raise TickerNotCoveredError(
            f"Ticker {symbol!r} is not present in SEC's company table. "
            "SEC coverage is limited to US-registered issuers."
        )

    filings = await fetch_recent_quarterly_filings(cik, limit=limit)

    result = AutoIngestResult(
        ticker=symbol,
        cik=cik,
        ingested=0,
        skipped_existing=0,
        failed=0,
    )

    for filing in filings:
        existing = await _find_existing(db, symbol, filing.accession_no)
        if existing is not None:
            result.skipped_existing += 1
            result.document_ids.append(existing.id)
            continue

        try:
            html_bytes = await fetch_filing_bytes(filing.primary_doc_url)
            text = extract_text_from_filing(html_bytes)
        except (EdgarUpstreamError, EdgarExtractionError) as e:
            # Don't poison the whole ingest — log, tally, move on.
            logger.warning(
                "auto-ingest failed for %s %s (%s): %s",
                symbol, filing.accession_no, filing.form, e,
            )
            result.failed += 1
            result.failures.append(
                AutoIngestFailure(
                    accession_no=filing.accession_no,
                    form=filing.form,
                    reason=str(e),
                )
            )
            continue

        row = ResearchDocument(
            ticker=symbol,
            filename=filing.primary_doc_name,
            storage_path=None,
            mime_type="text/html",
            file_size_bytes=len(html_bytes),
            extracted_text=text,
            extracted_text_tokens_estimate=estimate_tokens(text),
            extraction_status="ready",
            extraction_error=None,
            uploaded_by_email=triggered_by_email,
            source="sec_auto",
            sec_accession_no=filing.accession_no,
            sec_form=filing.form,
            sec_period_of_report=filing.period_of_report,
            external_url=filing.primary_doc_url,
        )
        db.add(row)
        try:
            await db.commit()
        except IntegrityError as e:
            # Race window: another request inserted the same accession
            # between our SELECT and INSERT. Roll back, count as
            # skipped (the other request already persisted it).
            await db.rollback()
            existing = await _find_existing(db, symbol, filing.accession_no)
            if existing is not None:
                result.skipped_existing += 1
                result.document_ids.append(existing.id)
            else:
                # IntegrityError with no findable row → genuinely failed
                # (e.g. a different constraint). Surface it.
                logger.warning(
                    "auto-ingest race-loss for %s %s: %s",
                    symbol, filing.accession_no, e,
                )
                result.failed += 1
                result.failures.append(
                    AutoIngestFailure(
                        accession_no=filing.accession_no,
                        form=filing.form,
                        reason=f"DB conflict: {e.orig if hasattr(e, 'orig') else e}",
                    )
                )
            continue

        result.ingested += 1
        result.document_ids.append(row.id)

    return result


async def _find_existing(
    db: AsyncSession,
    ticker: str,
    accession_no: str,
) -> Optional[ResearchDocument]:
    """Look up an existing sec_auto row by (ticker, accession_no).
    Returns None if no row exists."""
    stmt = select(ResearchDocument).where(
        ResearchDocument.ticker == ticker,
        ResearchDocument.sec_accession_no == accession_no,
    )
    res = await db.execute(stmt)
    return res.scalar_one_or_none()
