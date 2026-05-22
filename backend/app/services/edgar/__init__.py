"""SEC EDGAR integration (Phase 18).

Resolves tickers to CIKs, fetches filings histories, and downloads
10-K / 10-Q primary documents. All modules respect SEC's fair-access
policy: required User-Agent header (via SEC_USER_AGENT env var) +
client-side rate limiting (<=10 req/sec).
"""
from app.services.edgar.ticker_lookup import (
    EdgarConfigError,
    EdgarUpstreamError,
    resolve_ticker,
)

__all__ = ["EdgarConfigError", "EdgarUpstreamError", "resolve_ticker"]
