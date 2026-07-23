"""Phase 18.4 — Auto-ingest orchestrator contract tests.

What these pin:
  - End-to-end happy path: 2 filings (mocked) → 2 ResearchDocument
    rows persisted with source='sec_auto', text extracted, dedup
    fields populated.
  - Idempotency: running auto-ingest twice for the same ticker
    yields 0 new ingests + N skipped_existing on the second run.
  - Partial failure: 1 filing downloads OK, 1 returns 404 → result
    reports 1 ingested + 1 failed + failures list with the reason.
  - Unknown ticker → TickerNotCoveredError → 404 at the endpoint.
  - SEC misconfig (empty SEC_USER_AGENT) → 503.
  - Endpoint auth required + ticker regex validated.
  - Endpoint surfaces the result counts + failure list intact.
"""
from __future__ import annotations

import secrets
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from sqlalchemy import select

from app.models.auth import EmailAllowlist
from app.models.document import ResearchDocument
from app.services.edgar.ticker_lookup import _reset_cache_for_tests


# Realistic NVIDIA ticker table + submissions response.
TICKER_TABLE = {
    "0": {"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA CORP"},
}

SUBMISSIONS_NVDA = {
    "cik": "0001045810",
    "filings": {
        "recent": {
            "accessionNumber": [
                "0001045810-26-000012",
                "0001045810-25-000045",
            ],
            "filingDate": ["2026-02-21", "2025-11-19"],
            "reportDate": ["2026-01-26", "2025-10-26"],
            "form": ["10-K", "10-Q"],
            "primaryDocument": ["nvda-20260126.htm", "nvda-20251026.htm"],
        }
    },
}

FILING_HTML = b"""<html><body>
<h1>NVIDIA CORPORATION</h1>
<p>Revenue for the quarter was $35.1B, up 94% YoY.</p>
</body></html>"""


def _sec_router(routes):
    """Pass-through wrapper that mocks only SEC URLs, leaving the
    FastAPI test client's internal httpx calls untouched. `routes` is
    a dict of substring → payload or (status, payload)."""
    original_get = httpx.AsyncClient.get

    async def fake_get(self, url, *args, **kwargs):
        url_str = str(url)
        if "sec.gov" not in url_str:
            return await original_get(self, url, *args, **kwargs)
        response = AsyncMock(spec=httpx.Response)
        for key, value in routes.items():
            if key in url_str:
                if isinstance(value, tuple):
                    status_code, payload = value
                else:
                    status_code, payload = 200, value
                response.status_code = status_code
                if isinstance(payload, bytes):
                    response.content = payload
                    response.json = lambda: {}
                else:
                    response.json = lambda p=payload: p
                    response.content = b""
                return response
        raise AssertionError(f"unexpected SEC URL: {url_str}")
    return fake_get


@pytest.fixture(autouse=True)
def _edgar_env(monkeypatch):
    from app.core import config as config_mod
    monkeypatch.setattr(
        config_mod.settings, "sec_user_agent", "FINRLX-Test test@example.com"
    )
    _reset_cache_for_tests()
    yield
    _reset_cache_for_tests()


@pytest.fixture(autouse=True)
async def _clean_research_documents():
    """The test DB is session-scoped and in-memory, so rows persist
    across tests. Each auto-ingest test asserts on specific
    ingested/skipped counts, so we wipe NVDA-related rows before
    each test."""
    from tests.conftest import test_session_factory
    from sqlalchemy import delete

    async with test_session_factory() as db:
        await db.execute(
            delete(ResearchDocument).where(ResearchDocument.ticker == "NVDA")
        )
        await db.commit()
    yield


# ── Service-level tests (direct call, no endpoint) ──────────────────


@pytest.mark.asyncio
async def test_auto_ingest_persists_new_filings():
    """Happy path: 2 fresh filings → 2 rows in research_documents."""
    from tests.conftest import test_session_factory
    from app.services.research.auto_ingest import auto_ingest_filings

    fake_get = _sec_router({
        "company_tickers.json": TICKER_TABLE,
        "submissions/CIK": SUBMISSIONS_NVDA,
        "/Archives/edgar/data/": FILING_HTML,
    })

    with patch.object(httpx.AsyncClient, "get", fake_get):
        async with test_session_factory() as db:
            result = await auto_ingest_filings(
                db,
                ticker="NVDA",
                triggered_by_email="op@finrlx.local",
            )

    assert result.ticker == "NVDA"
    assert result.cik == "0001045810"
    assert result.ingested == 2
    assert result.skipped_existing == 0
    assert result.failed == 0
    assert len(result.document_ids) == 2

    # Verify the rows landed correctly.
    async with test_session_factory() as db:
        rows = (
            await db.execute(
                select(ResearchDocument).where(ResearchDocument.ticker == "NVDA")
            )
        ).scalars().all()

    nvda_auto = [r for r in rows if r.source == "sec_auto"]
    assert len(nvda_auto) == 2
    accessions = {r.sec_accession_no for r in nvda_auto}
    assert "0001045810-26-000012" in accessions
    assert "0001045810-25-000045" in accessions
    for r in nvda_auto:
        assert r.storage_path is None
        assert r.external_url.startswith("https://www.sec.gov/")
        assert "NVIDIA CORPORATION" in (r.extracted_text or "")
        assert r.extraction_status == "ready"
        assert r.uploaded_by_email == "op@finrlx.local"


@pytest.mark.asyncio
async def test_auto_ingest_is_idempotent():
    """Second run for the same ticker → 0 ingested + 2 skipped."""
    from tests.conftest import test_session_factory
    from app.services.research.auto_ingest import auto_ingest_filings

    fake_get = _sec_router({
        "company_tickers.json": TICKER_TABLE,
        "submissions/CIK": SUBMISSIONS_NVDA,
        "/Archives/edgar/data/": FILING_HTML,
    })

    with patch.object(httpx.AsyncClient, "get", fake_get):
        async with test_session_factory() as db:
            first = await auto_ingest_filings(
                db, ticker="NVDA", triggered_by_email="op@finrlx.local"
            )
        async with test_session_factory() as db:
            second = await auto_ingest_filings(
                db, ticker="NVDA", triggered_by_email="op@finrlx.local"
            )

    assert first.ingested == 2
    assert second.ingested == 0
    assert second.skipped_existing == 2
    # document_ids should reference the SAME rows from the first run.
    assert set(first.document_ids) == set(second.document_ids)


@pytest.mark.asyncio
async def test_auto_ingest_partial_failure_continues():
    """1 filing 404s on download, the other succeeds → result has
    1 ingested + 1 failed, with failure details."""
    from tests.conftest import test_session_factory
    from app.services.research.auto_ingest import auto_ingest_filings

    # Route the FIRST accession (the 10-K) to a 404, second to success.
    bad_accession = "0001045810-26-000012"
    good_accession = "0001045810-25-000045"

    original_get = httpx.AsyncClient.get

    async def fake_get(self, url, *args, **kwargs):
        url_str = str(url)
        if "sec.gov" not in url_str:
            return await original_get(self, url, *args, **kwargs)
        response = AsyncMock(spec=httpx.Response)
        if "company_tickers.json" in url_str:
            response.status_code = 200
            response.json = lambda: TICKER_TABLE
            return response
        if "submissions/CIK" in url_str:
            response.status_code = 200
            response.json = lambda: SUBMISSIONS_NVDA
            return response
        if "/Archives/edgar/data/" in url_str:
            if bad_accession.replace("-", "") in url_str:
                response.status_code = 404
                response.content = b""
                return response
            response.status_code = 200
            response.content = FILING_HTML
            return response
        raise AssertionError(f"unexpected URL: {url_str}")

    with patch.object(httpx.AsyncClient, "get", fake_get):
        async with test_session_factory() as db:
            result = await auto_ingest_filings(
                db, ticker="NVDA", triggered_by_email="op@finrlx.local"
            )

    assert result.ingested == 1
    assert result.failed == 1
    assert result.skipped_existing == 0
    assert len(result.failures) == 1
    assert result.failures[0].accession_no == bad_accession
    assert "404" in result.failures[0].reason or "no submissions" in result.failures[0].reason.lower() or "Failed" in result.failures[0].reason
    # The good accession persisted.
    async with test_session_factory() as db:
        good_row = (
            await db.execute(
                select(ResearchDocument).where(
                    ResearchDocument.sec_accession_no == good_accession
                )
            )
        ).scalar_one_or_none()
    assert good_row is not None


@pytest.mark.asyncio
async def test_auto_ingest_unknown_ticker_raises():
    """Ticker not in SEC's table → TickerNotCoveredError."""
    from tests.conftest import test_session_factory
    from app.services.research.auto_ingest import (
        TickerNotCoveredError,
        auto_ingest_filings,
    )

    fake_get = _sec_router({"company_tickers.json": TICKER_TABLE})

    with patch.object(httpx.AsyncClient, "get", fake_get):
        async with test_session_factory() as db:
            with pytest.raises(TickerNotCoveredError):
                await auto_ingest_filings(
                    db, ticker="ZZZZZ", triggered_by_email="op@finrlx.local"
                )


# ── Endpoint-level tests ────────────────────────────────────────────


async def _signup_user(client) -> str:
    from tests.conftest import test_session_factory

    email = f"ingest-{secrets.token_hex(4)}@example.com"
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


@pytest.mark.asyncio
async def test_endpoint_requires_auth(anon_client):
    r = await anon_client.post("/api/v1/research/NVDA/auto-ingest")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_endpoint_invalid_ticker_400(client):
    token = await _signup_user(client)
    r = await client.post(
        "/api/v1/research/123-bad/auto-ingest",
        headers=_bearer(token),
    )
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_endpoint_happy_path_returns_counts(client):
    token = await _signup_user(client)

    fake_get = _sec_router({
        "company_tickers.json": TICKER_TABLE,
        "submissions/CIK": SUBMISSIONS_NVDA,
        "/Archives/edgar/data/": FILING_HTML,
    })
    with patch.object(httpx.AsyncClient, "get", fake_get):
        r = await client.post(
            "/api/v1/research/NVDA/auto-ingest",
            headers=_bearer(token),
        )

    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["ticker"] == "NVDA"
    assert data["cik"] == "0001045810"
    assert data["ingested"] == 2
    assert data["skipped_existing"] == 0
    assert data["failed"] == 0
    assert len(data["document_ids"]) == 2
    assert data["failures"] == []


@pytest.mark.asyncio
async def test_endpoint_unknown_ticker_returns_404(client):
    token = await _signup_user(client)
    fake_get = _sec_router({"company_tickers.json": TICKER_TABLE})

    with patch.object(httpx.AsyncClient, "get", fake_get):
        r = await client.post(
            "/api/v1/research/ZZZZZ/auto-ingest",
            headers=_bearer(token),
        )

    assert r.status_code == 404, r.text


@pytest.mark.asyncio
async def test_endpoint_missing_sec_user_agent_returns_503(client, monkeypatch):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "sec_user_agent", "")
    _reset_cache_for_tests()

    token = await _signup_user(client)

    # No SEC URL should be hit before the config error fires.
    original_get = httpx.AsyncClient.get

    async def fake_get(self, url, *args, **kwargs):
        url_str = str(url)
        if "sec.gov" in url_str:
            raise AssertionError("endpoint reached SEC without UA")
        return await original_get(self, url, *args, **kwargs)

    with patch.object(httpx.AsyncClient, "get", fake_get):
        r = await client.post(
            "/api/v1/research/NVDA/auto-ingest",
            headers=_bearer(token),
        )

    assert r.status_code == 503, r.text
    assert "misconfigured" in r.text.lower() or "SEC_USER_AGENT" in r.text


@pytest.mark.asyncio
async def test_endpoint_limit_param_caps_ingest(client):
    token = await _signup_user(client)

    fake_get = _sec_router({
        "company_tickers.json": TICKER_TABLE,
        "submissions/CIK": SUBMISSIONS_NVDA,
        "/Archives/edgar/data/": FILING_HTML,
    })
    with patch.object(httpx.AsyncClient, "get", fake_get):
        r = await client.post(
            "/api/v1/research/NVDA/auto-ingest?limit=1",
            headers=_bearer(token),
        )

    assert r.status_code == 200, r.text
    assert r.json()["data"]["ingested"] == 1
