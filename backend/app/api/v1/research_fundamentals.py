"""Research Fundamentals + Peers API (Phase 16.0).

Two endpoints back the per-ticker workspace at /research/[ticker]:

    GET /api/v1/research/fundamentals/{ticker}
        -> FundamentalsResponse  (200, never 503; falls back to stub
           envelope so the frontend can always render the panel chrome)

    GET /api/v1/research/peers/{ticker}
        -> PeersResponse         (same contract — 200 with empty peers
           + coverage_note when no provider is configured)

    GET /api/v1/research/fundamentals/_status
        -> ProviderStatus        (diagnostics — does NOT hit the provider)

Both endpoints are unauthenticated for parity with the rest of the
/research/* surface (Phase 6 ticker workspace is anonymous-readable).
If we ever need auth, add `Depends(get_current_user)` here only — the
provider layer does not see request context.

Phase 16.0 SHIP TARGET — endpoints work end-to-end with the stub
provider. Phase 16.2 swaps the Finnhub shim for real HTTP calls; this
file does not change between phases.
"""
from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, status

from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.services.fundamentals import (
    FundamentalsResponse,
    PeersResponse,
    get_provider,
    get_provider_status,
)


router = APIRouter()

# Matches Yahoo-style symbols only.  Mirrors the frontend regex in
# frontend/src/lib/search.ts so the two sides agree on what's a "ticker".
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


# NOTE: static routes (`/_status`) MUST be declared before dynamic ones
# (`/{ticker}`) — FastAPI matches in declaration order, so the dynamic
# route would otherwise swallow the static path and the ticker regex
# would 400 on "_status".


@router.get(
    "/research/fundamentals/_status",
    response_model=ApiResponse[dict],
)
async def fundamentals_status() -> ApiResponse[dict]:
    """Diagnostics — does NOT call the provider; cheap to poll."""
    s = get_provider_status()
    return ApiResponse(
        meta=make_meta(),
        data={
            "configured": s.configured,
            "provider": s.provider_name,
            "detail": s.detail,
        },
    )


@router.get(
    "/research/fundamentals/{ticker}",
    response_model=ApiResponse[FundamentalsResponse],
)
async def get_fundamentals(ticker: str) -> ApiResponse[FundamentalsResponse]:
    """Return the fundamentals envelope for a single ticker."""
    symbol = _validate_ticker(ticker)
    provider = get_provider()
    if provider is None:
        # Router never returns None in Phase 16.0 (it falls back to the
        # stub), but the guard stays so future provider changes that
        # tighten the router don't silently 500 here.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fundamentals provider available.",
        )
    payload = await provider.get_fundamentals(symbol)
    return ApiResponse(meta=make_meta(), data=payload)


@router.get(
    "/research/peers/{ticker}",
    response_model=ApiResponse[PeersResponse],
)
async def get_peers(ticker: str) -> ApiResponse[PeersResponse]:
    """Return the sector-peers envelope for a single ticker."""
    symbol = _validate_ticker(ticker)
    provider = get_provider()
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fundamentals provider available.",
        )
    payload = await provider.get_peers(symbol)
    return ApiResponse(meta=make_meta(), data=payload)
