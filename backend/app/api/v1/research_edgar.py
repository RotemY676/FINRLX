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

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.auth_deps import get_current_user
from app.api.deps import make_meta
from app.models.auth import User
from app.schemas.common import ApiResponse
from app.services.edgar import (
    EdgarConfigError,
    EdgarUpstreamError,
    fetch_recent_quarterly_filings,
    resolve_ticker,
)

router = APIRouter()


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
