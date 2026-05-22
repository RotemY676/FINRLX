"""Phase 18.0 — Ticker → CIK resolver.

SEC EDGAR identifies companies by CIK (Central Index Key), a numeric
ID assigned at registration. To look up a company's filings we must
first translate a stock ticker (e.g. "NVDA") to its CIK (e.g.
1045810, formatted as "0001045810" in EDGAR URLs).

Data source: https://www.sec.gov/files/company_tickers.json — the
authoritative public mapping. Format:

    {
      "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
      "1": {"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA CORP"},
      ...
    }

Cache: the table changes very rarely (new IPOs, name changes), so we
load it once and refresh after `SEC_TICKER_CACHE_TTL_SECONDS` (default
7 days). The cache is module-level, lazy-loaded on first call,
serialized by an asyncio.Lock so concurrent first-callers don't trigger
duplicate SEC requests.

User-Agent: SEC's fair-access policy requires every request to carry
a real contact in the User-Agent header. Missing or generic UA strings
get rate-limited or blocked. We refuse to make the call when
`SEC_USER_AGENT` is empty, raising EdgarConfigError so the failure is
obvious in dev rather than mysterious in prod.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

import httpx

from app.core.config import settings


_TICKER_TABLE_URL = "https://www.sec.gov/files/company_tickers.json"
_REQUEST_TIMEOUT_SECONDS = 15.0


class EdgarConfigError(RuntimeError):
    """Raised when SEC_USER_AGENT (or other required config) is missing.

    Distinct from EdgarUpstreamError because it's an operator-fixable
    misconfiguration, not a transient network issue."""


class EdgarUpstreamError(RuntimeError):
    """Raised when SEC EDGAR returns an unusable response (network
    error, non-200 status, malformed JSON). Distinct from "ticker not
    found" — which is a successful lookup that returns None."""


@dataclass
class _CacheState:
    """Module-level cache. `mapping` is ticker (uppercase) → CIK
    (10-digit zero-padded string). `loaded_at` is the unix timestamp
    of the last successful load; we refresh after TTL elapses.

    A single asyncio.Lock serializes refreshes so concurrent
    cold-cache callers don't all hit SEC at once."""
    mapping: dict[str, str]
    loaded_at: float
    lock: asyncio.Lock


_cache = _CacheState(mapping={}, loaded_at=0.0, lock=asyncio.Lock())


def _format_cik(cik_int: int) -> str:
    """EDGAR URLs require zero-padded 10-digit CIKs (e.g. 320193 →
    '0000320193'). The data API also accepts the unpadded form, but
    we standardize on padded so callers can use the value directly
    in URLs without re-formatting."""
    return f"{cik_int:010d}"


async def _fetch_ticker_table() -> dict[str, str]:
    """Pull `company_tickers.json` from SEC and reshape into
    {TICKER_UPPER: CIK_10_DIGIT}. Raises EdgarUpstreamError on
    network / parse failure."""
    user_agent = (settings.sec_user_agent or "").strip()
    if not user_agent:
        raise EdgarConfigError(
            "SEC_USER_AGENT is empty. SEC requires a User-Agent header "
            "of the form 'AppName operator@example.com' on every "
            "request. Set the env var before calling EDGAR services."
        )

    headers = {
        "User-Agent": user_agent,
        "Accept": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
            resp = await client.get(_TICKER_TABLE_URL, headers=headers)
    except httpx.HTTPError as e:
        raise EdgarUpstreamError(
            f"Failed to reach SEC ticker table: {e}"
        ) from e

    if resp.status_code != 200:
        raise EdgarUpstreamError(
            f"SEC ticker table returned status {resp.status_code}. "
            "If this is 403, check that SEC_USER_AGENT contains a real "
            "contact email (SEC blocks generic / empty UAs)."
        )

    try:
        payload = resp.json()
    except ValueError as e:
        raise EdgarUpstreamError(
            "SEC ticker table returned non-JSON body."
        ) from e

    if not isinstance(payload, dict):
        raise EdgarUpstreamError(
            f"SEC ticker table has unexpected shape (not a dict): {type(payload).__name__}"
        )

    mapping: dict[str, str] = {}
    for row in payload.values():
        if not isinstance(row, dict):
            continue
        ticker = row.get("ticker")
        cik_int = row.get("cik_str")
        if not isinstance(ticker, str) or not isinstance(cik_int, int):
            continue
        mapping[ticker.upper()] = _format_cik(cik_int)
    return mapping


async def _ensure_cache_fresh() -> dict[str, str]:
    """Return the cached mapping, refreshing it if cold or expired.
    Concurrent callers serialize on the lock so SEC sees at most one
    in-flight refresh."""
    now = time.time()
    ttl = settings.sec_ticker_cache_ttl_seconds
    if _cache.mapping and (now - _cache.loaded_at) < ttl:
        return _cache.mapping

    async with _cache.lock:
        # Re-check inside the lock — another coroutine may have just
        # refreshed it while we were waiting.
        now = time.time()
        if _cache.mapping and (now - _cache.loaded_at) < ttl:
            return _cache.mapping
        mapping = await _fetch_ticker_table()
        _cache.mapping = mapping
        _cache.loaded_at = now
        return mapping


async def resolve_ticker(ticker: str) -> str | None:
    """Translate a stock ticker (any case) to a 10-digit CIK string.

    Returns None if the ticker is not present in SEC's table (i.e. the
    company is not US-listed / not registered with SEC). The caller
    should surface this as "SEC coverage only for US-listed
    securities" to the user.

    Raises:
      - EdgarConfigError when SEC_USER_AGENT is unset.
      - EdgarUpstreamError when SEC is unreachable or returns garbage.
    """
    if not ticker or not ticker.strip():
        return None
    normalized = ticker.strip().upper()
    mapping = await _ensure_cache_fresh()
    return mapping.get(normalized)


def _reset_cache_for_tests() -> None:
    """Test-only: clear cache state so a fresh load happens on the
    next call. Production code should never invoke this."""
    _cache.mapping = {}
    _cache.loaded_at = 0.0
