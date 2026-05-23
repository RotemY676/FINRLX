"""Phase 20.3 — asset autocomplete endpoint.

GET /api/v1/assets?q=...&limit=...

Powers the ticker-autocomplete on the /universe Add-asset modal. Read-only;
does NOT create assets. Search is case-insensitive, prefix-first, with
substring matches on ticker and name as a fallback to fill the budget.

The seeded test DB ships AAPL + MSFT, so most tests probe those.
"""
import pytest


@pytest.mark.asyncio
async def test_empty_query_returns_assets(client):
    """Empty q is treated as "browse all" — useful for the picker's
    initial open state. Returns up to `limit` assets, alphabetical."""
    r = await client.get("/api/v1/assets")
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) >= 2  # at least the seeded AAPL + MSFT
    tickers = [a["ticker"] for a in data]
    # Result must be alphabetically sorted within the active set.
    assert tickers == sorted(tickers)


@pytest.mark.asyncio
async def test_prefix_match_returns_aapl(client):
    r = await client.get("/api/v1/assets?q=AA")
    assert r.status_code == 200
    data = r.json()["data"]
    tickers = [a["ticker"] for a in data]
    assert "AAPL" in tickers
    # AAPL must be the first result (prefix match outranks substring).
    assert tickers[0] == "AAPL"


@pytest.mark.asyncio
async def test_query_is_case_insensitive(client):
    upper = await client.get("/api/v1/assets?q=AAPL")
    lower = await client.get("/api/v1/assets?q=aapl")
    mixed = await client.get("/api/v1/assets?q=AaPl")
    assert (
        upper.status_code == lower.status_code == mixed.status_code == 200
    )
    pick = lambda r: [a["ticker"] for a in r.json()["data"]]  # noqa: E731
    assert pick(upper) == pick(lower) == pick(mixed)


@pytest.mark.asyncio
async def test_substring_fallback_matches_name(client):
    """Querying "Microsoft" should surface MSFT via the name-substring
    tier even though the ticker doesn't start with M-I-C-R-O."""
    r = await client.get("/api/v1/assets?q=Microsoft")
    assert r.status_code == 200
    tickers = [a["ticker"] for a in r.json()["data"]]
    assert "MSFT" in tickers


@pytest.mark.asyncio
async def test_limit_param_is_honored(client):
    r = await client.get("/api/v1/assets?limit=1")
    assert r.status_code == 200
    assert len(r.json()["data"]) == 1


@pytest.mark.asyncio
async def test_limit_clamped_to_100(client):
    r = await client.get("/api/v1/assets?limit=101")
    # Pydantic Query(le=100) rejects values above 100 with 422 — clearer
    # than silently clamping.
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_response_includes_metadata_fields(client):
    r = await client.get("/api/v1/assets?q=AAPL")
    assert r.status_code == 200
    item = r.json()["data"][0]
    assert {"asset_id", "ticker", "name", "sector", "is_active"}.issubset(item.keys())


@pytest.mark.asyncio
async def test_no_match_returns_empty_list(client):
    r = await client.get("/api/v1/assets?q=NOSUCHTICKERZZZZZZZ")
    assert r.status_code == 200
    assert r.json()["data"] == []
