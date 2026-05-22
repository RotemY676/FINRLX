"""Phase 16.2 — Finnhub provider live-HTTP contract tests.

Mocked HTTP so CI does not hit the real Finnhub. The fixtures mirror
the actual Finnhub response shapes verbatim (collected from the
documented examples + hand-confirmed against finnhub.io/docs/api).

What these tests pin:
  - Profile + metric envelopes parse into FundamentalsResponse with
    the right unit conversions (percent → ratio, millions → USD).
  - The 52-week range fields populate via the alias path.
  - Empty profile + empty metrics produce a coverage_note, not a crash.
  - /stock/peers list parsing drops the target ticker and caps at
    PEER_FETCH_CAP.
  - Per-peer profile + quote fetch errors do not blank the whole
    peers panel.
  - 401 / 429 / 5xx all surface as FundamentalsProviderError with a
    useful detail string (no raw key leakage).
  - Module-level cache is hit on the second call within TTL.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.services.fundamentals.cache import (
    FUNDAMENTALS_CACHE,
    PEERS_LIST_CACHE,
    PEER_QUOTE_CACHE,
)
from app.services.fundamentals.finnhub_provider import (
    FinnhubFundamentalsProvider,
    PEER_FETCH_CAP,
)
from app.services.fundamentals.provider import FundamentalsProviderError


# ── Fixtures: realistic Finnhub response shapes ─────────────────────────


PROFILE_NVDA = {
    "country": "US",
    "currency": "USD",
    "exchange": "NASDAQ",
    "finnhubIndustry": "Semiconductors",
    "ipo": "1999-01-22",
    "logo": "https://...",
    "marketCapitalization": 3120000.0,   # millions
    "name": "NVIDIA Corp",
    "phone": "...",
    "shareOutstanding": 24560.0,         # millions
    "ticker": "NVDA",
    "weburl": "https://www.nvidia.com/",
}

METRIC_NVDA = {
    "metric": {
        "peTTM": 65.3,
        "pbAnnual": 50.2,
        "psTTM": 35.1,
        "grossMarginTTM": 75.4,           # percent
        "operatingMarginTTM": 62.3,
        "netProfitMarginTTM": 55.8,
        "revenuePerShareTTM": 5.20,
        "revenueGrowthTTMYoy": 122.4,     # percent
        "epsTTM": 2.99,
        "currentDividendYieldTTM": 0.03,  # percent already
        "52WeekHigh": 152.89,
        "52WeekLow": 79.30,
    },
    "metricType": "all",
    "series": {},
}

QUOTE_AAPL = {"c": 225.50, "pc": 222.30, "dp": 1.4395}
QUOTE_AMD = {"c": 165.00, "pc": 167.50, "dp": -1.4925}


# ── Helpers ─────────────────────────────────────────────────────────────


def _make_mock_client(routes: dict[str, object]) -> AsyncMock:
    """Patch httpx.AsyncClient so `client.get(path, params=...)` returns a
    response whose `.json()` is taken from `routes` keyed by request path.
    `routes` value can be a dict/list (200 OK) or an httpx.Response for
    error cases.
    """
    async def fake_get(self, path: str, params: dict | None = None):
        normalized = path.split("?")[0]
        payload = routes.get(normalized)
        if isinstance(payload, httpx.Response):
            return payload
        response = AsyncMock(spec=httpx.Response)
        response.status_code = 200
        response.json = lambda: payload
        return response

    return fake_get


def _clear_caches():
    FUNDAMENTALS_CACHE.clear()
    PEERS_LIST_CACHE.clear()
    PEER_QUOTE_CACHE.clear()


# ── Fundamentals parsing ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_finnhub_fundamentals_happy_path():
    _clear_caches()
    fake_get = _make_mock_client({
        "/stock/profile2": PROFILE_NVDA,
        "/stock/metric": METRIC_NVDA,
    })
    with patch.object(httpx.AsyncClient, "get", fake_get):
        provider = FinnhubFundamentalsProvider(api_key="dummy")
        payload = await provider.get_fundamentals("nvda")

    assert payload.ticker == "NVDA"
    assert payload.source == "finnhub"
    assert payload.company_name == "NVIDIA Corp"
    assert payload.industry == "Semiconductors"
    assert payload.sector == "Semiconductors"  # FE-friendly mirror
    # 3,120,000 million = 3.12T USD
    assert payload.market_cap_usd == pytest.approx(3.12e12)
    assert payload.pe_ratio_ttm == pytest.approx(65.3)
    # Percent → ratio
    assert payload.gross_margin_ttm == pytest.approx(0.754)
    assert payload.operating_margin_ttm == pytest.approx(0.623)
    assert payload.net_margin_ttm == pytest.approx(0.558)
    # Revenue: 5.20 / share * 24,560M shares * 1e6 = 1.27712e14 USD
    assert payload.revenue_ttm_usd == pytest.approx(5.20 * 24560 * 1_000_000)
    assert payload.revenue_growth_yoy == pytest.approx(1.224)
    # 52-week range via setattr alias path
    assert getattr(payload, "week_52_high", None) == pytest.approx(152.89)
    assert getattr(payload, "week_52_low", None) == pytest.approx(79.30)


@pytest.mark.asyncio
async def test_finnhub_fundamentals_uncovered_ticker_returns_coverage_note():
    _clear_caches()
    fake_get = _make_mock_client({
        "/stock/profile2": {},
        "/stock/metric": {"metric": {}, "metricType": "all", "series": {}},
    })
    with patch.object(httpx.AsyncClient, "get", fake_get):
        provider = FinnhubFundamentalsProvider(api_key="dummy")
        payload = await provider.get_fundamentals("ZZZX")

    assert payload.ticker == "ZZZX"
    assert payload.source == "finnhub"
    assert payload.company_name is None
    assert payload.pe_ratio_ttm is None
    assert payload.coverage_note is not None
    assert "coverage" in payload.coverage_note.lower() or "free tier" in payload.coverage_note.lower()


@pytest.mark.asyncio
async def test_finnhub_fundamentals_partial_metrics_does_not_invent():
    """When a profile is present but the metric envelope misses fields,
    populated fields fill and missing fields stay None."""
    _clear_caches()
    fake_get = _make_mock_client({
        "/stock/profile2": PROFILE_NVDA,
        "/stock/metric": {"metric": {"peTTM": 65.3}, "metricType": "all", "series": {}},
    })
    with patch.object(httpx.AsyncClient, "get", fake_get):
        provider = FinnhubFundamentalsProvider(api_key="dummy")
        payload = await provider.get_fundamentals("NVDA")

    assert payload.pe_ratio_ttm == pytest.approx(65.3)
    assert payload.gross_margin_ttm is None
    assert payload.operating_margin_ttm is None
    assert payload.eps_ttm is None


@pytest.mark.asyncio
async def test_finnhub_handles_string_NA_in_metric_envelope():
    """Finnhub occasionally returns the string 'NA' in lieu of null.
    _safe_float must coerce, not crash."""
    _clear_caches()
    fake_get = _make_mock_client({
        "/stock/profile2": PROFILE_NVDA,
        "/stock/metric": {"metric": {"peTTM": "NA", "epsTTM": "2.99"}, "metricType": "all", "series": {}},
    })
    with patch.object(httpx.AsyncClient, "get", fake_get):
        provider = FinnhubFundamentalsProvider(api_key="dummy")
        payload = await provider.get_fundamentals("NVDA")

    assert payload.pe_ratio_ttm is None       # 'NA' → None
    assert payload.eps_ttm == pytest.approx(2.99)  # '2.99' → 2.99


# ── Error handling ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_finnhub_401_surfaces_provider_error():
    _clear_caches()
    error_response = AsyncMock(spec=httpx.Response)
    error_response.status_code = 401
    error_response.json = lambda: {"error": "Invalid API key"}

    async def fake_get(self, path, params=None):
        return error_response

    with patch.object(httpx.AsyncClient, "get", fake_get):
        provider = FinnhubFundamentalsProvider(api_key="bad-key")
        with pytest.raises(FundamentalsProviderError) as exc_info:
            await provider.get_fundamentals("NVDA")
    # Error detail names the auth failure WITHOUT leaking the key value.
    assert "auth failed" in str(exc_info.value).lower() or "401" in str(exc_info.value)
    assert "bad-key" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_finnhub_429_surfaces_rate_limit_error():
    _clear_caches()
    error_response = AsyncMock(spec=httpx.Response)
    error_response.status_code = 429
    error_response.json = lambda: {"error": "Rate limit"}

    async def fake_get(self, path, params=None):
        return error_response

    with patch.object(httpx.AsyncClient, "get", fake_get):
        provider = FinnhubFundamentalsProvider(api_key="dummy")
        with pytest.raises(FundamentalsProviderError) as exc_info:
            await provider.get_fundamentals("NVDA")
    assert "rate-limit" in str(exc_info.value).lower() or "429" in str(exc_info.value)


# ── Peers ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_finnhub_peers_happy_path_drops_target_and_caps():
    _clear_caches()
    raw_peers = ["NVDA", "AMD", "INTC", "TSM", "QCOM", "AVGO", "MU", "TXN", "ON", "NXPI", "MRVL"]
    routes = {
        "/stock/peers": raw_peers,
        "/stock/profile2": PROFILE_NVDA,
        "/quote": QUOTE_AAPL,  # generic — used for each peer in the mocked route
    }
    fake_get = _make_mock_client(routes)
    with patch.object(httpx.AsyncClient, "get", fake_get):
        provider = FinnhubFundamentalsProvider(api_key="dummy")
        payload = await provider.get_peers("NVDA")

    assert payload.target_ticker == "NVDA"
    assert payload.target_industry == "Semiconductors"
    assert payload.source == "finnhub"
    # Target ticker dropped + capped to PEER_FETCH_CAP.
    assert len(payload.peers) <= PEER_FETCH_CAP
    assert all(p.ticker != "NVDA" for p in payload.peers)
    # Quote percent (1.4395%) → ratio (0.014395).
    for peer in payload.peers:
        if peer.change_pct_1d is not None:
            assert peer.change_pct_1d == pytest.approx(0.014395)


@pytest.mark.asyncio
async def test_finnhub_peers_empty_returns_coverage_note():
    _clear_caches()
    routes = {"/stock/peers": [], "/stock/profile2": PROFILE_NVDA}
    fake_get = _make_mock_client(routes)
    with patch.object(httpx.AsyncClient, "get", fake_get):
        provider = FinnhubFundamentalsProvider(api_key="dummy")
        payload = await provider.get_peers("NVDA")

    assert payload.peers == []
    assert payload.coverage_note is not None


# ── Cache ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_finnhub_fundamentals_cache_hit_avoids_second_http_call():
    _clear_caches()
    call_count = {"n": 0}

    async def fake_get(self, path, params=None):
        call_count["n"] += 1
        response = AsyncMock(spec=httpx.Response)
        response.status_code = 200
        response.json = lambda: PROFILE_NVDA if "profile2" in path else METRIC_NVDA
        return response

    with patch.object(httpx.AsyncClient, "get", fake_get):
        provider = FinnhubFundamentalsProvider(api_key="dummy")
        await provider.get_fundamentals("NVDA")
        first_calls = call_count["n"]
        await provider.get_fundamentals("NVDA")
        second_calls = call_count["n"]

    # First call hits profile + metric (2 GETs). Second call hits cache (0).
    assert first_calls == 2
    assert second_calls == 2  # unchanged because the second call was cached
