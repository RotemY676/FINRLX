"""Finnhub fundamentals + peers provider (Phase 16.2 — live HTTP).

Real HTTP implementation. Free tier: 60 calls/minute, single API key.

Endpoints used:
  - GET /api/v1/stock/profile2?symbol=TICKER  → company name, sector,
    industry, market cap, share count, ipo, weburl
  - GET /api/v1/stock/metric?symbol=TICKER&metric=all  → all valuation,
    profitability, growth ratios
  - GET /api/v1/stock/peers?symbol=TICKER  → list[str] of sector peers
  - GET /api/v1/quote?symbol=TICKER  → c (current), pc (previous close),
    dp (percent change)

All calls go through `httpx.AsyncClient` with a 10s timeout. Failures
raise `FundamentalsProviderError` so the caller can decide whether to
fall back to a cached row or 502 the client.

Caching is module-level (see `cache.py`): 6h fundamentals, 24h peer
list, 5min per-peer quote. Combined with the 60/min free-tier budget,
this gives a comfortable safety margin even with multiple concurrent
users.

Coverage notes:
  - Finnhub's free tier covers US equities well; non-US partial.
  - When the API returns an empty payload for a ticker, we surface
    `coverage_note` with a human explanation instead of raising.
  - `metric=all` is sometimes missing individual fields — we read
    defensively via `.get()` and leave the field None if absent.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

import httpx

from app.services.fundamentals.cache import (
    FUNDAMENTALS_CACHE,
    PEER_QUOTE_CACHE,
    PEERS_LIST_CACHE,
)
from app.services.fundamentals.provider import (
    FundamentalsProvider,
    FundamentalsProviderError,
)
from app.services.fundamentals.types import (
    FundamentalsResponse,
    PeerEntry,
    PeersResponse,
)

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
DEFAULT_TIMEOUT_S = 10.0
PEER_FETCH_CAP = 8  # surface no more than this many peers in the UI


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _safe_float(d: dict[str, Any], key: str) -> float | None:
    """Read a numeric metric defensively. Finnhub returns floats, ints,
    None, or sometimes the literal string 'NA' — we coerce everything
    to Optional[float] without crashing."""
    val = d.get(key)
    if val is None:
        return None
    if isinstance(val, int | float):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val)
        except ValueError:
            return None
    return None


def _safe_str(d: dict[str, Any], key: str) -> str | None:
    val = d.get(key)
    if isinstance(val, str) and val.strip():
        return val.strip()
    return None


def _pct_to_ratio(v: float | None) -> float | None:
    """Finnhub returns ratios as percentages (e.g. 12.34 = 12.34%). We
    convert to ratio (0..1) so frontend formatters can multiply by 100
    uniformly across providers."""
    return v / 100.0 if v is not None else None


class FinnhubFundamentalsProvider(FundamentalsProvider):
    """Phase 16.2 — live Finnhub HTTP calls + module-level cache."""

    name: str = "finnhub"
    IS_STUB: bool = False

    def __init__(self, api_key: str) -> None:
        # Captured at construction. Never logged. Passed as `token=`
        # query parameter (Finnhub's documented auth pattern).
        self._api_key = api_key

    def _make_client(self) -> httpx.AsyncClient:
        # New client per call is fine at our volume. The async context
        # manager in callers releases the connection promptly.
        return httpx.AsyncClient(
            base_url=FINNHUB_BASE_URL,
            timeout=DEFAULT_TIMEOUT_S,
        )

    async def _get_json(
        self,
        client: httpx.AsyncClient,
        path: str,
        **params: Any,
    ) -> Any:
        """Single GET → parsed JSON. Returns whatever Finnhub returns
        (dict for most endpoints, list for /stock/peers).

        Raises FundamentalsProviderError on network / auth / rate-limit
        / parse failures so the endpoint layer can handle them once.
        """
        params = {**params, "token": self._api_key}
        try:
            response = await client.get(path, params=params)
        except httpx.RequestError as e:
            raise FundamentalsProviderError(f"finnhub network error: {e}") from e
        if response.status_code == 401:
            raise FundamentalsProviderError(
                "finnhub auth failed (invalid or expired API key)"
            )
        if response.status_code == 429:
            raise FundamentalsProviderError(
                "finnhub rate-limit hit (60 calls/min on free tier)"
            )
        if response.status_code >= 400:
            raise FundamentalsProviderError(
                f"finnhub HTTP {response.status_code} on {path}"
            )
        try:
            return response.json()
        except ValueError as e:
            raise FundamentalsProviderError(
                f"finnhub returned invalid JSON on {path}: {e}"
            ) from e

    # ── Fundamentals ──────────────────────────────────────────────

    async def get_fundamentals(self, ticker: str) -> FundamentalsResponse:
        symbol = ticker.upper()
        cached = FUNDAMENTALS_CACHE.get(symbol)
        if cached is not None:
            return cached  # type: ignore[no-any-return]

        async with self._make_client() as client:
            profile_task = self._get_json(client, "/stock/profile2", symbol=symbol)
            metric_task = self._get_json(client, "/stock/metric", symbol=symbol, metric="all")
            profile, metric_envelope = await asyncio.gather(profile_task, metric_task)

        if not isinstance(profile, dict):
            profile = {}
        if not isinstance(metric_envelope, dict):
            metric_envelope = {}

        # Finnhub returns {} for unknown US tickers and {"name": "...", ...}
        # for covered ones. The metric envelope shape is
        # {"metric": {...}, "metricType": "all", "series": {...}}.
        is_covered = bool(profile.get("name"))
        metrics: dict[str, Any] = metric_envelope.get("metric") or {}

        if not is_covered and not metrics:
            response = FundamentalsResponse(
                ticker=symbol,
                source="finnhub",
                cached_at=_now_iso(),
                coverage_note=(
                    "Finnhub returned no profile or metrics for this ticker. "
                    "The free tier coverage focuses on US equities; international "
                    "tickers may need a paid plan or a different provider."
                ),
            )
            FUNDAMENTALS_CACHE.set(symbol, response)
            return response

        company_name = _safe_str(profile, "name")
        # Finnhub uses `finnhubIndustry` for industry; sector isn't always
        # present on the free profile2 endpoint, so we surface industry as
        # both `sector` and `industry` for the FE's "show what we have" rule.
        industry = _safe_str(profile, "finnhubIndustry")
        market_cap_m = _safe_float(profile, "marketCapitalization")
        market_cap_usd = market_cap_m * 1_000_000 if market_cap_m is not None else None

        revenue_per_share = _safe_float(metrics, "revenuePerShareTTM")
        shares_m = _safe_float(profile, "shareOutstanding")
        revenue_ttm_usd: float | None = None
        if revenue_per_share is not None and shares_m is not None:
            revenue_ttm_usd = revenue_per_share * shares_m * 1_000_000

        response = FundamentalsResponse(
            ticker=symbol,
            company_name=company_name,
            sector=industry,
            industry=industry,
            description=None,
            market_cap_usd=market_cap_usd,
            pe_ratio_ttm=_safe_float(metrics, "peTTM"),
            # Forward P/E: Finnhub free tier does NOT expose a real
            # forward P/E (which needs analyst consensus EPS). Earlier
            # this fell back to `peExclExtraAnnual` (annual P/E ex-
            # extraordinary items), which is NOT a forward metric and
            # produced misleading values like 274× for NVDA. Leaving
            # this None until either (a) we upgrade to a Finnhub plan
            # that exposes consensus EPS, or (b) we add a second
            # provider that does.
            forward_pe=_safe_float(metrics, "forwardPE"),
            price_to_book=_safe_float(metrics, "pbAnnual"),
            price_to_sales_ttm=_safe_float(metrics, "psTTM"),
            ev_to_ebitda=_safe_float(metrics, "currentEv/freeCashFlowTTM"),
            gross_margin_ttm=_pct_to_ratio(_safe_float(metrics, "grossMarginTTM")),
            operating_margin_ttm=_pct_to_ratio(_safe_float(metrics, "operatingMarginTTM")),
            net_margin_ttm=_pct_to_ratio(_safe_float(metrics, "netProfitMarginTTM")),
            revenue_ttm_usd=revenue_ttm_usd,
            revenue_growth_yoy=_pct_to_ratio(
                _safe_float(metrics, "revenueGrowthTTMYoy")
            ),
            eps_ttm=_safe_float(metrics, "epsTTM"),
            dividend_yield=_pct_to_ratio(
                _safe_float(metrics, "currentDividendYieldTTM")
            ),
            as_of=None,  # Finnhub metric envelope doesn't carry per-metric as_of
            source="finnhub",
            cached_at=_now_iso(),
            coverage_note=None,
        )
        # Pydantic alias-by-name for the 52-week range — assign by alias
        # after construction so the model_config populate_by_name keeps
        # both spellings consistent.
        response.week_52_high = _safe_float(metrics, "52WeekHigh")
        response.week_52_low = _safe_float(metrics, "52WeekLow")

        FUNDAMENTALS_CACHE.set(symbol, response)
        return response

    # ── Peers ─────────────────────────────────────────────────────

    async def get_peers(self, ticker: str) -> PeersResponse:
        symbol = ticker.upper()
        cached = PEERS_LIST_CACHE.get(symbol)
        if cached is not None:
            return cached  # type: ignore[no-any-return]

        async with self._make_client() as client:
            peers_raw = await self._get_json(client, "/stock/peers", symbol=symbol)
            peer_tickers_all = peers_raw if isinstance(peers_raw, list) else []

            # Drop the target symbol itself (Finnhub includes it) and
            # cap the surface so we don't blow the rate budget.
            peer_tickers: list[str] = [
                t for t in peer_tickers_all
                if isinstance(t, str) and t.upper() != symbol
            ][:PEER_FETCH_CAP]

            target_profile_task = self._get_json(client, "/stock/profile2", symbol=symbol)
            peer_snapshot_tasks = [
                self._fetch_peer_snapshot(client, t) for t in peer_tickers
            ]
            target_profile, *peer_snapshots = await asyncio.gather(
                target_profile_task,
                *peer_snapshot_tasks,
                return_exceptions=True,
            )

        # Bubble target-profile failures (auth, rate-limit) but not
        # per-peer ones (a single 500 shouldn't blank the whole list).
        if isinstance(target_profile, BaseException):
            raise target_profile  # type: ignore[misc]
        target_profile_dict = target_profile if isinstance(target_profile, dict) else {}
        target_industry = _safe_str(target_profile_dict, "finnhubIndustry")

        peers: list[PeerEntry] = []
        for snap in peer_snapshots:
            if isinstance(snap, BaseException):
                continue
            if snap is None:
                continue
            peers.append(snap)

        response = PeersResponse(
            target_ticker=symbol,
            target_sector=target_industry,
            target_industry=target_industry,
            peers=peers,
            as_of=None,
            source="finnhub",
            cached_at=_now_iso(),
            coverage_note=(
                None if peers else
                "Finnhub returned no peers for this ticker. Coverage is "
                "strongest for US equities; international tickers may not "
                "have a peer set."
            ),
        )
        PEERS_LIST_CACHE.set(symbol, response)
        return response

    async def _fetch_peer_snapshot(
        self,
        client: httpx.AsyncClient,
        peer_ticker: str,
    ) -> PeerEntry | None:
        """Fetch profile + quote for a peer. Result cached 5 min so the
        same peer across multiple target tickers doesn't refetch."""
        cached = PEER_QUOTE_CACHE.get(peer_ticker)
        if cached is not None:
            return cached  # type: ignore[no-any-return]

        try:
            profile_task = self._get_json(client, "/stock/profile2", symbol=peer_ticker)
            quote_task = self._get_json(client, "/quote", symbol=peer_ticker)
            profile, quote = await asyncio.gather(profile_task, quote_task)
        except FundamentalsProviderError:
            return None

        profile_dict = profile if isinstance(profile, dict) else {}
        quote_dict = quote if isinstance(quote, dict) else {}

        current = _safe_float(quote_dict, "c")
        prev_close = _safe_float(quote_dict, "pc")
        change_pct = _safe_float(quote_dict, "dp")
        change_ratio = change_pct / 100.0 if change_pct is not None else None

        market_cap_m = _safe_float(profile_dict, "marketCapitalization")
        market_cap_usd = market_cap_m * 1_000_000 if market_cap_m is not None else None

        # If neither name nor price came back, the peer is uncovered —
        # skip the row entirely rather than render nulls.
        if not profile_dict.get("name") and current is None:
            return None

        entry = PeerEntry(
            ticker=peer_ticker.upper(),
            name=_safe_str(profile_dict, "name"),
            sector=_safe_str(profile_dict, "finnhubIndustry"),
            industry=_safe_str(profile_dict, "finnhubIndustry"),
            market_cap_usd=market_cap_usd,
            last_close_usd=current if current is not None else prev_close,
            change_pct_1d=change_ratio,
            change_pct_ytd=None,  # not in the free /quote endpoint
        )
        PEER_QUOTE_CACHE.set(peer_ticker, entry)
        return entry
