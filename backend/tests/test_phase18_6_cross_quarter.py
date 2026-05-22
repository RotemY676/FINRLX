"""Phase 18.6 — Cross-quarter insights service + endpoints.

What these pin:
  - Service: loads sec_auto documents in chronological order, builds
    the prompt, calls the LLM chain, persists a TickerInsights row.
  - Service: raises InsufficientFilingsError when ticker has no
    sec_auto docs ready.
  - Service: budget check fires BEFORE the LLM call.
  - Service: chain fallback works (gemini fails → anthropic succeeds).
  - Endpoint POST: 200 happy path, 400 invalid ticker, 409 no docs,
    503 on budget/chain failure, auth required.
  - Endpoint GET: returns null when no insights yet, returns latest
    after POST.
"""
from __future__ import annotations

import secrets
from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import delete, select

from app.models.auth import EmailAllowlist
from app.models.document import ResearchDocument
from app.models.ticker_insights import TickerInsights
from app.services.llm.types import LLMResponse


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
async def _clean_tables():
    """Wipe both insights + documents between tests so counts are
    deterministic. The in-memory DB persists across the session."""
    from tests.conftest import test_session_factory

    async with test_session_factory() as db:
        await db.execute(delete(TickerInsights))
        await db.execute(delete(ResearchDocument).where(ResearchDocument.ticker.in_(["NVDA", "MSFT", "ZZZZ"])))
        await db.commit()
    yield


async def _seed_sec_auto_docs(ticker: str = "NVDA", n: int = 3):
    """Insert N sec_auto documents with realistic chronological
    period_of_report dates."""
    from tests.conftest import test_session_factory

    async with test_session_factory() as db:
        for i in range(n):
            db.add(
                ResearchDocument(
                    ticker=ticker,
                    filename=f"{ticker.lower()}-q{i}.htm",
                    storage_path=None,
                    mime_type="text/html",
                    file_size_bytes=1000,
                    extracted_text=(
                        f"Filing {i}: Revenue was ${(i + 1) * 10}B. "
                        f"Gross margin {70 + i}%. CEO commented on growth."
                    ),
                    extraction_status="ready",
                    uploaded_by_email="auto@finrlx.local",
                    source="sec_auto",
                    sec_accession_no=f"0001045810-25-{i:06d}",
                    sec_form="10-Q" if i % 2 == 0 else "10-K",
                    sec_period_of_report=date(2025, 1 + i * 3, 26),
                    external_url=f"https://www.sec.gov/Archives/edgar/data/1045810/.../{i}.htm",
                )
            )
        await db.commit()


def _mock_llm_provider(text: str = "## Headline\n\nRevenue grew."):
    """Return a fake provider with .chat returning a canned LLMResponse."""
    fake = AsyncMock()
    fake.name = "gemini"
    fake.chat = AsyncMock(
        return_value=LLMResponse(
            text=text,
            provider="gemini",
            model="gemini-2.5-flash",
            input_tokens=15000,
            output_tokens=800,
        )
    )
    return fake


def _allow_budget():
    """Bypass the budget check for tests that aren't testing budget."""
    from app.services.documents import budget as budget_svc

    async def _ok(_db, _projected):
        return True, budget_svc.BudgetStatus(
            year=2026, month=5, cap_tokens=999_999,
            used_tokens=0, remaining_tokens=999_999,
            cost_estimate_usd=0.0, per_provider={}, over_budget=False,
        )
    return _ok


# ── Service-level tests ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_insights_persists_a_row(monkeypatch):
    """Happy path: 3 sec_auto docs exist → service builds prompt,
    calls LLM, persists a TickerInsights row with the LLM's text +
    list of accessions covered."""
    from app.services.documents import budget as budget_svc
    from app.services.research import cross_quarter_analyze
    from app.services.research.cross_quarter_analyze import generate_insights
    from tests.conftest import test_session_factory

    monkeypatch.setattr(budget_svc, "can_spend", _allow_budget())
    monkeypatch.setattr(
        cross_quarter_analyze, "get_provider_chain",
        lambda: [_mock_llm_provider("## Headline\n\nRevenue rose 50% YoY.")]
    )
    # Also stub record_usage so the test doesn't depend on DB state
    # for budget tracking (the budget table is empty in our test setup).
    async def _no_op_record(_db, *, provider, input_tokens, output_tokens):
        pass
    monkeypatch.setattr(budget_svc, "record_usage", _no_op_record)

    await _seed_sec_auto_docs("NVDA", n=3)

    async with test_session_factory() as db:
        result = await generate_insights(
            db, ticker="NVDA", triggered_by_email="op@finrlx.local"
        )

    assert result.insights.ticker == "NVDA"
    assert "Revenue rose" in result.insights.summary_text
    assert len(result.insights.quarters_covered) == 3
    assert result.insights.provider == "gemini"
    assert result.insights.input_tokens == 15000
    assert result.insights.output_tokens == 800

    # Verify it actually committed.
    async with test_session_factory() as db:
        rows = (
            await db.execute(select(TickerInsights).where(TickerInsights.ticker == "NVDA"))
        ).scalars().all()
    assert len(rows) == 1


# ── Phase 18.6.1 — Structured metrics JSON parsing ──────────────────


def test_parse_metrics_block_happy_path():
    from app.services.research.cross_quarter_analyze import _parse_metrics_block

    text = (
        '```json\n'
        '{\n'
        '  "metrics": [\n'
        '    {\n'
        '      "name": "Revenue",\n'
        '      "unit": "USD millions",\n'
        '      "quarters": [\n'
        '        {"period_end": "2025-01-26", "label": "Q4 FY25", "value": 39331},\n'
        '        {"period_end": "2025-04-27", "label": "Q1 FY26", "value": 44062}\n'
        '      ]\n'
        '    }\n'
        '  ]\n'
        '}\n'
        '```\n\n## Latest-quarter delta\n\nRevenue grew.'
    )
    parsed = _parse_metrics_block(text)
    assert parsed is not None
    assert len(parsed["metrics"]) == 1
    m = parsed["metrics"][0]
    assert m["name"] == "Revenue"
    assert m["unit"] == "USD millions"
    assert len(m["quarters"]) == 2
    assert m["quarters"][0]["value"] == 39331.0
    assert m["quarters"][0]["label"] == "Q4 FY25"


def test_parse_metrics_block_drops_invalid_metrics():
    """A single bad metric shouldn't poison the whole block —
    valid metrics still come through."""
    from app.services.research.cross_quarter_analyze import _parse_metrics_block

    text = (
        '```json\n'
        '{"metrics": [\n'
        '  {"name": "Revenue", "unit": "USD", "quarters": [{"period_end": "2025-01-26", "label": "Q4", "value": 100}]},\n'
        '  "garbage",\n'
        '  {"name": "NoQuarters"},\n'
        '  {"name": "BadValue", "quarters": [{"value": "not a number"}]}\n'
        ']}\n'
        '```'
    )
    parsed = _parse_metrics_block(text)
    assert parsed is not None
    assert len(parsed["metrics"]) == 1
    assert parsed["metrics"][0]["name"] == "Revenue"


def test_parse_metrics_block_returns_none_when_no_fence():
    from app.services.research.cross_quarter_analyze import _parse_metrics_block

    assert _parse_metrics_block("just markdown, no JSON block") is None


def test_parse_metrics_block_returns_none_for_invalid_json():
    """Malformed JSON inside the fence → None (the caller falls back
    to narrative-only mode rather than blowing up)."""
    from app.services.research.cross_quarter_analyze import _parse_metrics_block

    text = '```json\n{not valid json\n```'
    assert _parse_metrics_block(text) is None


def test_strip_metrics_block_removes_only_the_fenced_block():
    from app.services.research.cross_quarter_analyze import _strip_metrics_block

    text = (
        '```json\n{"metrics": []}\n```\n\n'
        '## Latest-quarter delta\n\nRevenue grew.\n\n'
        '## What to watch\n\nMargin.'
    )
    stripped = _strip_metrics_block(text)
    assert "```" not in stripped
    assert "Latest-quarter delta" in stripped
    assert "What to watch" in stripped


@pytest.mark.asyncio
async def test_generate_insights_persists_metrics_when_llm_emits_json(monkeypatch):
    """End-to-end: when the LLM response contains a JSON block, the
    persisted row carries `metrics` AND `summary_text` has the JSON
    stripped out."""
    from app.services.documents import budget as budget_svc
    from app.services.research import cross_quarter_analyze
    from app.services.research.cross_quarter_analyze import generate_insights
    from tests.conftest import test_session_factory

    monkeypatch.setattr(budget_svc, "can_spend", _allow_budget())
    async def _no_op_record(_db, *, provider, input_tokens, output_tokens):
        pass
    monkeypatch.setattr(budget_svc, "record_usage", _no_op_record)

    llm_text = (
        '```json\n'
        '{"metrics": [{"name": "Revenue", "unit": "USD millions", '
        '"quarters": [{"period_end": "2025-01-26", "label": "Q4 FY25", "value": 39331}]}]}\n'
        '```\n\n'
        '## Latest-quarter delta\n\nRevenue grew.'
    )
    monkeypatch.setattr(
        cross_quarter_analyze, "get_provider_chain",
        lambda: [_mock_llm_provider(llm_text)]
    )

    await _seed_sec_auto_docs("NVDA", n=2)

    async with test_session_factory() as db:
        result = await generate_insights(
            db, ticker="NVDA", triggered_by_email="op@finrlx.local"
        )

    assert result.insights.metrics is not None
    assert len(result.insights.metrics["metrics"]) == 1
    assert result.insights.metrics["metrics"][0]["name"] == "Revenue"
    # Narrative no longer contains the JSON fence.
    assert "```" not in result.insights.summary_text
    assert "Latest-quarter delta" in result.insights.summary_text


@pytest.mark.asyncio
async def test_generate_insights_persists_without_metrics_when_no_json(monkeypatch):
    """When the LLM doesn't emit a JSON block, the row still persists
    with metrics=None — the chart just won't appear on the FE."""
    from app.services.documents import budget as budget_svc
    from app.services.research import cross_quarter_analyze
    from app.services.research.cross_quarter_analyze import generate_insights
    from tests.conftest import test_session_factory

    monkeypatch.setattr(budget_svc, "can_spend", _allow_budget())
    async def _no_op_record(_db, *, provider, input_tokens, output_tokens):
        pass
    monkeypatch.setattr(budget_svc, "record_usage", _no_op_record)
    monkeypatch.setattr(
        cross_quarter_analyze, "get_provider_chain",
        lambda: [_mock_llm_provider("## Latest-quarter delta\n\nNo JSON here.")]
    )

    await _seed_sec_auto_docs("NVDA", n=1)

    async with test_session_factory() as db:
        result = await generate_insights(
            db, ticker="NVDA", triggered_by_email="op@finrlx.local"
        )

    assert result.insights.metrics is None
    assert "No JSON here" in result.insights.summary_text


@pytest.mark.asyncio
async def test_generate_insights_raises_when_no_docs_ready():
    """Ticker with NO sec_auto docs → InsufficientFilingsError."""
    from app.services.research.cross_quarter_analyze import (
        InsufficientFilingsError,
        generate_insights,
    )
    from tests.conftest import test_session_factory

    async with test_session_factory() as db:
        with pytest.raises(InsufficientFilingsError):
            await generate_insights(
                db, ticker="ZZZZ", triggered_by_email="op@finrlx.local"
            )


@pytest.mark.asyncio
async def test_generate_insights_falls_back_when_first_provider_fails(monkeypatch):
    """Chain fallback: gemini errors → anthropic succeeds."""
    from app.services.documents import budget as budget_svc
    from app.services.research import cross_quarter_analyze
    from app.services.research.cross_quarter_analyze import generate_insights
    from app.services.llm.provider import StubProviderError
    from tests.conftest import test_session_factory

    monkeypatch.setattr(budget_svc, "can_spend", _allow_budget())
    async def _no_op_record(_db, *, provider, input_tokens, output_tokens):
        pass
    monkeypatch.setattr(budget_svc, "record_usage", _no_op_record)

    failing = AsyncMock()
    failing.name = "gemini"
    failing.chat = AsyncMock(side_effect=StubProviderError("gemini rate-limit"))

    succeeding = AsyncMock()
    succeeding.name = "anthropic"
    succeeding.chat = AsyncMock(
        return_value=LLMResponse(
            text="## Headline\nFallback worked.",
            provider="anthropic",
            model="claude-sonnet-4-6",
            input_tokens=15000,
            output_tokens=400,
        )
    )
    monkeypatch.setattr(
        cross_quarter_analyze, "get_provider_chain",
        lambda: [failing, succeeding],
    )

    await _seed_sec_auto_docs("NVDA", n=2)

    async with test_session_factory() as db:
        result = await generate_insights(
            db, ticker="NVDA", triggered_by_email="op@finrlx.local"
        )

    assert result.provider == "anthropic"
    assert "Fallback worked" in result.insights.summary_text
    failing.chat.assert_awaited_once()
    succeeding.chat.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_latest_insights_returns_newest():
    from app.services.research.cross_quarter_analyze import get_latest_insights
    from tests.conftest import test_session_factory
    from datetime import datetime, timezone, timedelta

    async with test_session_factory() as db:
        db.add(
            TickerInsights(
                ticker="NVDA",
                summary_text="older",
                quarters_covered=["acc-1"],
                provider="gemini",
                model="gemini-2.5-flash",
                generated_at=datetime.now(timezone.utc) - timedelta(days=5),
                generated_by_email="op@finrlx.local",
            )
        )
        db.add(
            TickerInsights(
                ticker="NVDA",
                summary_text="newer",
                quarters_covered=["acc-1", "acc-2"],
                provider="gemini",
                model="gemini-2.5-flash",
                generated_at=datetime.now(timezone.utc) - timedelta(hours=1),
                generated_by_email="op@finrlx.local",
            )
        )
        await db.commit()

    async with test_session_factory() as db:
        row = await get_latest_insights(db, ticker="NVDA")
    assert row is not None
    assert row.summary_text == "newer"


@pytest.mark.asyncio
async def test_get_latest_insights_returns_none_when_empty():
    from app.services.research.cross_quarter_analyze import get_latest_insights
    from tests.conftest import test_session_factory

    async with test_session_factory() as db:
        row = await get_latest_insights(db, ticker="MSFT")
    assert row is None


# ── Endpoint-level tests ────────────────────────────────────────────


async def _signup_user(client) -> str:
    from tests.conftest import test_session_factory

    email = f"insights-{secrets.token_hex(4)}@example.com"
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
async def test_post_insights_requires_auth(client):
    r = await client.post("/api/v1/research/NVDA/insights")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_post_insights_invalid_ticker_400(client):
    token = await _signup_user(client)
    r = await client.post(
        "/api/v1/research/bad-ticker/insights", headers=_bearer(token)
    )
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_post_insights_409_when_no_docs(client):
    token = await _signup_user(client)
    r = await client.post(
        "/api/v1/research/ZZZZ/insights", headers=_bearer(token)
    )
    assert r.status_code == 409, r.text
    assert "auto-ingest" in r.text.lower() or "ready" in r.text.lower()


@pytest.mark.asyncio
async def test_post_insights_happy_path(client, monkeypatch):
    from app.services.documents import budget as budget_svc
    from app.services.research import cross_quarter_analyze

    monkeypatch.setattr(budget_svc, "can_spend", _allow_budget())
    async def _no_op_record(_db, *, provider, input_tokens, output_tokens):
        pass
    monkeypatch.setattr(budget_svc, "record_usage", _no_op_record)
    monkeypatch.setattr(
        cross_quarter_analyze, "get_provider_chain",
        lambda: [_mock_llm_provider("Generated insights text.")]
    )

    token = await _signup_user(client)
    await _seed_sec_auto_docs("NVDA", n=2)

    r = await client.post(
        "/api/v1/research/NVDA/insights", headers=_bearer(token)
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["ticker"] == "NVDA"
    assert "Generated insights text" in data["summary_text"]
    assert len(data["quarters_covered"]) == 2
    assert data["provider"] == "gemini"


@pytest.mark.asyncio
async def test_get_insights_returns_null_when_empty(client):
    token = await _signup_user(client)
    r = await client.get(
        "/api/v1/research/MSFT/insights", headers=_bearer(token)
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"] is None


@pytest.mark.asyncio
async def test_get_insights_returns_latest_after_post(client, monkeypatch):
    from app.services.documents import budget as budget_svc
    from app.services.research import cross_quarter_analyze

    monkeypatch.setattr(budget_svc, "can_spend", _allow_budget())
    async def _no_op_record(_db, *, provider, input_tokens, output_tokens):
        pass
    monkeypatch.setattr(budget_svc, "record_usage", _no_op_record)
    monkeypatch.setattr(
        cross_quarter_analyze, "get_provider_chain",
        lambda: [_mock_llm_provider("Latest insights.")]
    )

    token = await _signup_user(client)
    await _seed_sec_auto_docs("NVDA", n=2)

    # POST first
    r1 = await client.post(
        "/api/v1/research/NVDA/insights", headers=_bearer(token)
    )
    assert r1.status_code == 200, r1.text

    # GET should now return that same content
    r2 = await client.get(
        "/api/v1/research/NVDA/insights", headers=_bearer(token)
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["data"] is not None
    assert "Latest insights" in r2.json()["data"]["summary_text"]
    assert r2.json()["data"]["id"] == r1.json()["data"]["id"]
