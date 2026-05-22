"""Phase 18.1 — /research/edgar/probe endpoint contract tests.

What these pin:
  - Auth required (401 without token).
  - Happy path: NVDA → 200 + cik + list of filings (mocked SEC).
  - Unknown ticker → 404 with a US-coverage hint.
  - Missing SEC_USER_AGENT → 503 with a clear misconfig message.
  - SEC upstream 403/network error → 503 with reason.
  - `limit` query param caps the result.
"""
from __future__ import annotations

import secrets
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.models.auth import EmailAllowlist
from app.services.edgar.ticker_lookup import _reset_cache_for_tests


# Minimal ticker table — only the entries the tests reference.
TICKER_TABLE = {
    "0": {"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA CORP"},
    "1": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
}

# Minimal submissions response — just enough for one 10-K and one 10-Q.
SUBMISSIONS_NVDA = {
    "cik": "0001045810",
    "filings": {
        "recent": {
            "accessionNumber": ["0001045810-26-000012", "0001045810-25-000045"],
            "filingDate": ["2026-02-21", "2025-11-19"],
            "reportDate": ["2026-01-26", "2025-10-26"],
            "form": ["10-K", "10-Q"],
            "primaryDocument": ["nvda-20260126.htm", "nvda-20251026.htm"],
        }
    },
}


async def _signup_user(client) -> str:
    """Create an allowlisted user and return its access token."""
    from tests.conftest import test_session_factory

    email = f"edgar-{secrets.token_hex(4)}@example.com"
    async with test_session_factory() as db:
        db.add(EmailAllowlist(email=email))
        await db.commit()
    r = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "a-strong-password-12345"},
    )
    assert r.status_code == 201, r.text
    return r.json()["tokens"]["access_token"]


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _route_sec_response(routes):
    """Patch httpx.AsyncClient.get so SEC URLs are mocked but the
    FastAPI test client's own httpx calls (to /api/v1/...) pass
    through to the original method. SEC URLs always include
    'sec.gov'; the test client uses relative paths starting with '/'.
    """
    original_get = httpx.AsyncClient.get

    async def fake_get(self, url, *args, **kwargs):
        url_str = str(url)
        if "sec.gov" not in url_str:
            # Pass-through for the FastAPI test client's own requests.
            return await original_get(self, url, *args, **kwargs)
        response = AsyncMock(spec=httpx.Response)
        for key, value in routes.items():
            if key in url_str:
                if isinstance(value, tuple):
                    status_code, payload = value
                else:
                    status_code, payload = 200, value
                response.status_code = status_code
                response.json = lambda p=payload: p
                return response
        raise AssertionError(f"unexpected SEC URL: {url_str}")
    return fake_get


@pytest.fixture(autouse=True)
def _edgar_test_env(monkeypatch):
    from app.core import config as config_mod

    monkeypatch.setattr(
        config_mod.settings, "sec_user_agent", "FINRLX-Test test@example.com"
    )
    _reset_cache_for_tests()
    yield
    _reset_cache_for_tests()


@pytest.mark.asyncio
async def test_probe_requires_auth(client):
    r = await client.get("/api/v1/research/edgar/probe?ticker=NVDA")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_probe_happy_path_returns_cik_and_filings(client):
    token = await _signup_user(client)

    fake_get = _route_sec_response({
        "company_tickers.json": TICKER_TABLE,
        "submissions/CIK": SUBMISSIONS_NVDA,
    })
    with patch.object(httpx.AsyncClient, "get", fake_get):
        r = await client.get(
            "/api/v1/research/edgar/probe?ticker=nvda",  # lowercase ok
            headers=_bearer(token),
        )

    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["ticker"] == "NVDA"
    assert data["cik"] == "0001045810"
    assert data["filings_count"] == 2
    assert {f["form"] for f in data["filings"]} == {"10-K", "10-Q"}
    assert data["filings"][0]["primary_doc_url"].startswith(
        "https://www.sec.gov/Archives/edgar/data/1045810/"
    )


@pytest.mark.asyncio
async def test_probe_limit_param_caps_results(client):
    token = await _signup_user(client)

    fake_get = _route_sec_response({
        "company_tickers.json": TICKER_TABLE,
        "submissions/CIK": SUBMISSIONS_NVDA,
    })
    with patch.object(httpx.AsyncClient, "get", fake_get):
        r = await client.get(
            "/api/v1/research/edgar/probe?ticker=NVDA&limit=1",
            headers=_bearer(token),
        )

    assert r.status_code == 200
    assert r.json()["data"]["filings_count"] == 1


@pytest.mark.asyncio
async def test_probe_unknown_ticker_returns_404(client):
    token = await _signup_user(client)

    fake_get = _route_sec_response({"company_tickers.json": TICKER_TABLE})
    with patch.object(httpx.AsyncClient, "get", fake_get):
        r = await client.get(
            "/api/v1/research/edgar/probe?ticker=ZZZZZ",
            headers=_bearer(token),
        )

    assert r.status_code == 404, r.text
    assert "US-registered" in r.text or "SEC" in r.text


@pytest.mark.asyncio
async def test_probe_missing_user_agent_returns_503(client, monkeypatch):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "sec_user_agent", "")
    _reset_cache_for_tests()

    token = await _signup_user(client)

    # The endpoint must not even reach SEC — pass through any test-client
    # calls but assert if SEC is contacted.
    original_get = httpx.AsyncClient.get

    async def fake_get(self, url, *args, **kwargs):
        url_str = str(url)
        if "sec.gov" in url_str:
            raise AssertionError("probe hit the network despite missing UA")
        return await original_get(self, url, *args, **kwargs)

    with patch.object(httpx.AsyncClient, "get", fake_get):
        r = await client.get(
            "/api/v1/research/edgar/probe?ticker=NVDA",
            headers=_bearer(token),
        )

    assert r.status_code == 503, r.text
    assert "SEC_USER_AGENT" in r.text or "misconfigured" in r.text


@pytest.mark.asyncio
async def test_probe_upstream_failure_returns_503(client):
    """SEC 403 from the ticker table → probe surfaces 503 with detail."""
    token = await _signup_user(client)

    fake_get = _route_sec_response({"company_tickers.json": (403, {})})
    with patch.object(httpx.AsyncClient, "get", fake_get):
        r = await client.get(
            "/api/v1/research/edgar/probe?ticker=NVDA",
            headers=_bearer(token),
        )

    assert r.status_code == 503, r.text
    assert "SEC" in r.text
