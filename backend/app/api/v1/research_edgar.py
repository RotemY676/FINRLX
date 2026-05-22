"""Phase 18 — SEC EDGAR endpoints.

Phase 18.1 ships ONE endpoint: a diagnostic probe so the operator can
verify against real SEC infrastructure that:
  (a) SEC_USER_AGENT is correctly set on the deploy
  (b) outbound traffic to data.sec.gov + www.sec.gov works from the
      backend host
  (c) the ticker → CIK resolver and the filings fetcher agree on the
      same identity

The probe is NOT part of the final user-facing flow — that comes in
Phase 18.4 (auto-ingest orchestrator) and 18.6 (insights). The probe
exists so we can flip each EDGAR module on in production with high
confidence before stacking the next phase on top.

Auth-gated so the endpoint isn't anonymously enumerable; we don't
want bots discovering "here's a free SEC proxy with a clean UA."
"""
from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_deps import get_current_user
from app.api.deps import make_meta
from app.core.database import get_db
from app.models.auth import User
from app.schemas.common import ApiResponse
from app.services.edgar import (
    EdgarConfigError,
    EdgarUpstreamError,
    fetch_recent_quarterly_filings,
    resolve_ticker,
)
from app.services.documents.analyze import BudgetExceededError
from app.services.llm.provider import StubProviderError
from app.services.research.auto_ingest import (
    TickerNotCoveredError,
    auto_ingest_filings,
)
from app.services.research.cross_quarter_analyze import (
    InsufficientFilingsError,
    generate_insights,
    get_latest_insights,
)

router = APIRouter()

# Mirrors the Phase 16 / 17.0 ticker regex used across the research surface.
_TICKER_RE = re.compile(r"^[A-Z]{1,8}(\.[A-Z]{1,4})?$")


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


@router.get(
    "/research/edgar/probe",
    response_model=ApiResponse[dict],
    summary="Diagnostic — resolve a ticker and list its last quarterly filings",
)
async def edgar_probe(
    ticker: str = Query(..., min_length=1, max_length=12, description="Stock ticker, any case"),
    limit: int = Query(6, ge=1, le=20, description="Max filings to return"),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    """Resolves the ticker → CIK, then fetches the last N quarterly
    filings. Returns the metadata only — no document downloads
    (those come in Phase 18.2).

    Status codes:
      - 200: ticker resolved and filings retrieved (filings list may
        be empty if the company has not filed any 10-K/10-Q).
      - 404: ticker not in SEC's table (non-US listing, or unknown).
      - 503: SEC_USER_AGENT misconfigured OR SEC unreachable.
        The body's `detail` field disambiguates which.
    """
    _ = user  # auth-required only; user identity not used in the response

    try:
        cik = await resolve_ticker(ticker)
    except EdgarConfigError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"EDGAR misconfigured: {e}",
        )
    except EdgarUpstreamError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"SEC unreachable: {e}",
        )

    if cik is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Ticker {ticker.upper()!r} is not present in SEC's "
                "company table. SEC coverage is limited to US-registered "
                "issuers; foreign listings (LSE, TASE, etc.) are not "
                "available via this surface."
            ),
        )

    try:
        filings = await fetch_recent_quarterly_filings(cik, limit=limit)
    except EdgarConfigError as e:
        # Should not happen here (resolve_ticker already passed UA check),
        # but defensive — caught for clarity in the response.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"EDGAR misconfigured: {e}",
        )
    except EdgarUpstreamError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"SEC submissions endpoint failed: {e}",
        )

    return ApiResponse(
        meta=make_meta(),
        data={
            "ticker": ticker.upper(),
            "cik": cik,
            "filings_count": len(filings),
            "filings": [
                {
                    "accession_no": f.accession_no,
                    "form": f.form,
                    "filing_date": f.filing_date.isoformat(),
                    "period_of_report": f.period_of_report.isoformat(),
                    "primary_doc_name": f.primary_doc_name,
                    "primary_doc_url": f.primary_doc_url,
                }
                for f in filings
            ],
        },
    )


@router.post(
    "/research/{ticker}/auto-ingest",
    response_model=ApiResponse[dict],
    summary="Auto-fetch last 6 quarterly filings from SEC and persist them",
)
async def auto_ingest(
    ticker: str = Path(..., min_length=1, max_length=12),
    limit: int = Query(6, ge=1, le=10, description="Max filings to ingest"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    """Resolve the ticker, fetch the last `limit` quarterly filings
    from SEC EDGAR, download + extract text from each, and persist as
    research_documents rows with source='sec_auto'.

    Idempotent: re-running this for the same ticker dedups via the
    (ticker, sec_accession_no) unique index — already-ingested
    filings are counted in `skipped_existing`, not re-downloaded.

    Status codes:
      - 200: orchestration finished; the response data shows how many
        rows were ingested vs skipped vs failed.
      - 400: ticker doesn't match the canonical regex.
      - 404: ticker not in SEC's table (non-US listing).
      - 503: SEC misconfigured (SEC_USER_AGENT empty) or SEC's
        submissions endpoint unreachable. Per-filing download
        failures do NOT cause 503 — they appear in `failures`.

    The request blocks until all filings are processed. Worst-case
    wall time ~30–60s for 6 fresh ingests (sequential SEC downloads,
    each capped at 50 MB). Use the existing GET /research/documents
    endpoint to inspect the persisted rows.
    """
    _ = user  # auth-required; user identity recorded via triggered_by_email
    symbol = _validate_ticker(ticker)

    try:
        result = await auto_ingest_filings(
            db,
            ticker=symbol,
            triggered_by_email=user.email,
            limit=limit,
        )
    except TickerNotCoveredError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except EdgarConfigError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"EDGAR misconfigured: {e}",
        )
    except EdgarUpstreamError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"SEC unreachable: {e}",
        )

    return ApiResponse(
        meta=make_meta(),
        data={
            "ticker": result.ticker,
            "cik": result.cik,
            "ingested": result.ingested,
            "skipped_existing": result.skipped_existing,
            "failed": result.failed,
            "failures": [
                {
                    "accession_no": f.accession_no,
                    "form": f.form,
                    "reason": f.reason,
                }
                for f in result.failures
            ],
            "document_ids": result.document_ids,
        },
    )


def _insights_to_dict(row) -> dict:
    """Shared serialization for both POST + GET insights endpoints."""
    return {
        "id": row.id,
        "ticker": row.ticker,
        "summary_text": row.summary_text,
        "quarters_covered": list(row.quarters_covered or []),
        "provider": row.provider,
        "model": row.model,
        "input_tokens": row.input_tokens,
        "output_tokens": row.output_tokens,
        "cost_estimate_usd": row.cost_estimate_usd,
        "generated_at": row.generated_at.isoformat(),
        "generated_by_email": row.generated_by_email,
    }


@router.post(
    "/research/{ticker}/insights",
    response_model=ApiResponse[dict],
    summary="Generate cross-quarter LLM insights for a ticker",
)
async def post_insights(
    ticker: str = Path(..., min_length=1, max_length=12),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    """Synthesize trajectory + latest-quarter-delta insights across
    the ticker's sec_auto documents. Persists a new TickerInsights row
    (history-preserving — does NOT overwrite previous insights).

    Pre-requisite: at least one sec_auto document with
    extraction_status='ready' must exist for the ticker. Call
    POST /research/{ticker}/auto-ingest first if needed.

    Status codes:
      - 200: insights generated + persisted.
      - 400: ticker doesn't match the canonical regex.
      - 409: no sec_auto documents ready for this ticker (run
        auto-ingest first).
      - 503: LLM provider chain exhausted, or monthly token budget
        would be exceeded.

    Wall time: typically 10–30s (one LLM call against the full
    cross-quarter prompt; ~80K tokens input on Gemini 2.5 Flash).
    """
    symbol = _validate_ticker(ticker)

    try:
        result = await generate_insights(
            db, ticker=symbol, triggered_by_email=user.email
        )
    except InsufficientFilingsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )
    except BudgetExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"Monthly LLM token budget would be exceeded "
                f"({e.status.used_tokens} used + {e.projected_tokens} projected > "
                f"{e.status.cap_tokens} cap). Wait for next month or raise "
                "MAX_MONTHLY_LLM_TOKENS."
            ),
        )
    except StubProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )

    return ApiResponse(
        meta=make_meta(),
        data=_insights_to_dict(result.insights),
    )


@router.get(
    "/research/{ticker}/insights",
    response_model=ApiResponse[dict | None],
    summary="Get the most recent insights for a ticker (null if none generated)",
)
async def get_insights(
    ticker: str = Path(..., min_length=1, max_length=12),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict | None]:
    """Return the most recent TickerInsights row for the ticker, or
    null if generation has never run. The FE checks `generated_at`
    against the 7-day TTL to decide whether to show "Stale, refresh?".

    Status codes:
      - 200: returns the insights row, or `data: null` if none exist.
      - 400: ticker doesn't match the canonical regex.
    """
    _ = user
    symbol = _validate_ticker(ticker)

    row = await get_latest_insights(db, ticker=symbol)
    return ApiResponse(
        meta=make_meta(),
        data=_insights_to_dict(row) if row is not None else None,
    )
