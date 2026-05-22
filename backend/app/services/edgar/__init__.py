"""SEC EDGAR integration (Phase 18).

Resolves tickers to CIKs, fetches filings histories, and downloads
10-K / 10-Q primary documents. All modules respect SEC's fair-access
policy: required User-Agent header (via SEC_USER_AGENT env var) +
client-side rate limiting (<=10 req/sec).
"""
from app.services.edgar.extraction import (
    EdgarExtractionError,
    extract_text_from_filing,
    fetch_filing_bytes,
)
from app.services.edgar.filings import EdgarFiling, fetch_recent_quarterly_filings
from app.services.edgar.ticker_lookup import (
    EdgarConfigError,
    EdgarUpstreamError,
    resolve_ticker,
)

__all__ = [
    "EdgarConfigError",
    "EdgarExtractionError",
    "EdgarFiling",
    "EdgarUpstreamError",
    "extract_text_from_filing",
    "fetch_filing_bytes",
    "fetch_recent_quarterly_filings",
    "resolve_ticker",
]
