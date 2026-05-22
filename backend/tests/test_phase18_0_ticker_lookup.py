"""Phase 18.0 — Ticker → CIK resolver contract tests.

What these pin:
  - Happy path: a known ticker (NVDA) resolves to its 10-digit
    zero-padded CIK.
  - Case + whitespace normalization (lowercase ticker, padded ticker,
    empty / whitespace input).
  - Unknown tickers return None (not an error).
  - SEC_USER_AGENT empty → EdgarConfigError BEFORE the network call.
  - Non-200 from SEC → EdgarUpstreamError (operator-facing detail).
  - Cache: the second call within TTL does NOT hit the network.
  - Cache TTL: setting TTL=0 forces a refresh on every call.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest


# Realistic SEC fixture — only the rows we test against.
SEC_TICKER_TABLE = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA CORP"},
    "2": {"cik_str": 789019, "ticker": "MSFT", "title": "MICROSOFT CORP"},
}


def _mock_sec_response(payload, status_code: int = 200):
    """Patch httpx.AsyncClient.get to return a single canned response.
    The patched function ignores URL/headers — Phase 18.0 only makes
    one request shape."""
    async def fake_get(self, url, headers=None):
        response = AsyncMock(spec=httpx.Response)
        response.status_code = status_code
        response.json = lambda: payload
        return response
    return fake_get


@pytest.fixture(autouse=True)
def _reset_cache_between_tests(monkeypatch):
    """Every test starts with a cold cache and a real-looking
    SEC_USER_AGENT (most tests need it set; the missing-UA test
    overrides this back to empty)."""
    from app.core import config as config_mod
    from app.services.edgar.ticker_lookup import _reset_cache_for_tests

    monkeypatch.setattr(
        config_mod.settings, "sec_user_agent", "FINRLX-Test test@example.com"
    )
    monkeypatch.setattr(config_mod.settings, "sec_ticker_cache_ttl_seconds", 60)
    _reset_cache_for_tests()
    yield
    _reset_cache_for_tests()


@pytest.mark.asyncio
async def test_resolve_known_ticker_returns_padded_cik():
    from app.services.edgar.ticker_lookup import resolve_ticker

    with patch.object(httpx.AsyncClient, "get", _mock_sec_response(SEC_TICKER_TABLE)):
        cik = await resolve_ticker("NVDA")

    # NVDA's CIK is 1045810 → padded to 10 digits.
    assert cik == "0001045810"


@pytest.mark.asyncio
async def test_resolve_lowercase_ticker_normalizes():
    from app.services.edgar.ticker_lookup import resolve_ticker

    with patch.object(httpx.AsyncClient, "get", _mock_sec_response(SEC_TICKER_TABLE)):
        cik = await resolve_ticker("nvda")

    assert cik == "0001045810"


@pytest.mark.asyncio
async def test_resolve_strips_whitespace():
    from app.services.edgar.ticker_lookup import resolve_ticker

    with patch.object(httpx.AsyncClient, "get", _mock_sec_response(SEC_TICKER_TABLE)):
        cik = await resolve_ticker("  AAPL  ")

    assert cik == "0000320193"


@pytest.mark.asyncio
async def test_resolve_unknown_ticker_returns_none():
    """A non-US ticker (or typo) is NOT an error — return None so the
    caller can surface 'SEC coverage only for US-listed' cleanly."""
    from app.services.edgar.ticker_lookup import resolve_ticker

    with patch.object(httpx.AsyncClient, "get", _mock_sec_response(SEC_TICKER_TABLE)):
        cik = await resolve_ticker("ZZZZZ")

    assert cik is None


@pytest.mark.asyncio
async def test_resolve_empty_input_returns_none():
    from app.services.edgar.ticker_lookup import resolve_ticker

    cik = await resolve_ticker("")
    assert cik is None

    cik = await resolve_ticker("   ")
    assert cik is None


@pytest.mark.asyncio
async def test_missing_user_agent_raises_config_error_before_network(monkeypatch):
    """If SEC_USER_AGENT is empty, we must NOT send a request to SEC
    (their fair-access policy would block / rate-limit anonymous UAs,
    poisoning future requests from the same IP). Raise immediately."""
    from app.core import config as config_mod
    from app.services.edgar.ticker_lookup import (
        EdgarConfigError,
        resolve_ticker,
    )

    monkeypatch.setattr(config_mod.settings, "sec_user_agent", "")

    # If a network call sneaks through, the mock will succeed and the
    # test will pass falsely. We patch get to assert it's never called.
    called = {"count": 0}

    async def fake_get(self, url, headers=None):
        called["count"] += 1
        raise AssertionError(
            "resolve_ticker hit the network despite missing SEC_USER_AGENT"
        )

    with patch.object(httpx.AsyncClient, "get", fake_get):
        with pytest.raises(EdgarConfigError) as exc_info:
            await resolve_ticker("NVDA")

    assert "SEC_USER_AGENT" in str(exc_info.value)
    assert called["count"] == 0


@pytest.mark.asyncio
async def test_sec_non_200_raises_upstream_error():
    """403 / 5xx from SEC → EdgarUpstreamError with operator-facing
    detail (especially the 403 hint about UA being too generic)."""
    from app.services.edgar.ticker_lookup import (
        EdgarUpstreamError,
        resolve_ticker,
    )

    with patch.object(httpx.AsyncClient, "get", _mock_sec_response({}, status_code=403)):
        with pytest.raises(EdgarUpstreamError) as exc_info:
            await resolve_ticker("NVDA")

    assert "403" in str(exc_info.value)


@pytest.mark.asyncio
async def test_sec_network_error_raises_upstream_error():
    from app.services.edgar.ticker_lookup import (
        EdgarUpstreamError,
        resolve_ticker,
    )

    async def fake_get(self, url, headers=None):
        raise httpx.ConnectError("name resolution failed")

    with patch.object(httpx.AsyncClient, "get", fake_get):
        with pytest.raises(EdgarUpstreamError) as exc_info:
            await resolve_ticker("NVDA")

    assert "Failed to reach SEC" in str(exc_info.value)


@pytest.mark.asyncio
async def test_cache_hit_avoids_second_network_call():
    """First resolve hits SEC; second resolve within TTL must NOT
    hit SEC again. We instrument the mock to count calls."""
    from app.services.edgar.ticker_lookup import resolve_ticker

    call_count = {"n": 0}

    async def counting_get(self, url, headers=None):
        call_count["n"] += 1
        response = AsyncMock(spec=httpx.Response)
        response.status_code = 200
        response.json = lambda: SEC_TICKER_TABLE
        return response

    with patch.object(httpx.AsyncClient, "get", counting_get):
        cik1 = await resolve_ticker("NVDA")
        cik2 = await resolve_ticker("AAPL")  # different ticker, same cache load
        cik3 = await resolve_ticker("NVDA")  # repeat

    assert cik1 == "0001045810"
    assert cik2 == "0000320193"
    assert cik3 == "0001045810"
    # ONE network call should serve all three resolutions.
    assert call_count["n"] == 1


@pytest.mark.asyncio
async def test_cache_ttl_zero_forces_refresh_every_call(monkeypatch):
    """TTL=0 means every resolution refreshes. Useful sanity check
    that the TTL gate is actually consulted (regression guard)."""
    from app.core import config as config_mod
    from app.services.edgar.ticker_lookup import resolve_ticker

    monkeypatch.setattr(config_mod.settings, "sec_ticker_cache_ttl_seconds", 0)

    call_count = {"n": 0}

    async def counting_get(self, url, headers=None):
        call_count["n"] += 1
        response = AsyncMock(spec=httpx.Response)
        response.status_code = 200
        response.json = lambda: SEC_TICKER_TABLE
        return response

    with patch.object(httpx.AsyncClient, "get", counting_get):
        await resolve_ticker("NVDA")
        await resolve_ticker("NVDA")
        await resolve_ticker("NVDA")

    assert call_count["n"] == 3


@pytest.mark.asyncio
async def test_malformed_sec_payload_raises_upstream_error():
    """If SEC returns valid JSON but in an unexpected shape, surface as
    EdgarUpstreamError (not a silent None / KeyError)."""
    from app.services.edgar.ticker_lookup import (
        EdgarUpstreamError,
        resolve_ticker,
    )

    with patch.object(httpx.AsyncClient, "get", _mock_sec_response(["not", "a", "dict"])):
        with pytest.raises(EdgarUpstreamError):
            await resolve_ticker("NVDA")


@pytest.mark.asyncio
async def test_resolve_skips_rows_with_missing_fields():
    """Real SEC data is generally well-formed but we should not crash
    if a row is missing cik_str or ticker — just skip it."""
    from app.services.edgar.ticker_lookup import resolve_ticker

    table = {
        "0": {"cik_str": 320193, "ticker": "AAPL"},
        "1": {"ticker": "MISSING_CIK"},          # no cik_str
        "2": {"cik_str": 999999},                # no ticker
        "3": "not even a dict",
        "4": {"cik_str": 1045810, "ticker": "NVDA"},
    }

    with patch.object(httpx.AsyncClient, "get", _mock_sec_response(table)):
        assert await resolve_ticker("AAPL") == "0000320193"
        assert await resolve_ticker("NVDA") == "0001045810"
        assert await resolve_ticker("MISSING_CIK") is None
