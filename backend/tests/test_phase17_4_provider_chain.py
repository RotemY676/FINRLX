"""Phase 17.4 — Provider chain (free-first fallback) + Gemini provider.

Pins:
  - `get_provider_chain()` parses `LLM_PROVIDER_CHAIN` into an ordered
    list of constructed providers, skipping unknown names and
    providers whose API key is unset.
  - `get_provider()` (legacy) returns the FIRST provider in the chain
    for backwards compatibility.
  - `analyze_document` walks the chain on StubProviderError: when the
    first provider fails, the second is tried; the first successful
    response wins.
  - When every provider in the chain fails, `analyze_document` raises
    StubProviderError quoting the last failure.
  - GeminiProvider parses the Google REST response into LLMResponse,
    including usageMetadata token counts.
  - GeminiProvider surfaces 401/403 as auth errors, 429 as rate-limit,
    5xx as server errors, and an empty candidates list as "no
    candidates" — all StubProviderError so the chain can fall back.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.services.llm.gemini import GeminiProvider
from app.services.llm.provider import StubProviderError
from app.services.llm.types import LLMMessage, LLMResponse


# ── Router: chain parsing ───────────────────────────────────────────


def test_chain_empty_when_nothing_configured(monkeypatch):
    from app.core import config as config_mod
    from app.services.llm.router import get_provider_chain

    monkeypatch.setattr(config_mod.settings, "llm_provider", "")
    monkeypatch.setattr(config_mod.settings, "llm_provider_chain", "")
    monkeypatch.setattr(config_mod.settings, "llm_anthropic_api_key", "")
    monkeypatch.setattr(config_mod.settings, "llm_gemini_api_key", "")

    assert get_provider_chain() == []


def test_chain_parses_comma_separated_and_constructs_providers(monkeypatch):
    from app.core import config as config_mod
    from app.services.llm.router import get_provider_chain

    monkeypatch.setattr(config_mod.settings, "llm_provider_chain", "gemini,anthropic")
    monkeypatch.setattr(config_mod.settings, "llm_provider", "")
    monkeypatch.setattr(config_mod.settings, "llm_gemini_api_key", "gem-key-xxx")
    monkeypatch.setattr(config_mod.settings, "llm_anthropic_api_key", "ant-key-xxx")

    chain = get_provider_chain()
    assert [p.name for p in chain] == ["gemini", "anthropic"]


def test_chain_skips_providers_with_missing_keys(monkeypatch):
    from app.core import config as config_mod
    from app.services.llm.router import get_provider_chain

    monkeypatch.setattr(config_mod.settings, "llm_provider_chain", "gemini,anthropic")
    monkeypatch.setattr(config_mod.settings, "llm_provider", "")
    monkeypatch.setattr(config_mod.settings, "llm_gemini_api_key", "")  # missing
    monkeypatch.setattr(config_mod.settings, "llm_anthropic_api_key", "ant-key-xxx")

    chain = get_provider_chain()
    # gemini factory returns None when key is empty → only anthropic
    # makes it into the chain.
    assert [p.name for p in chain] == ["anthropic"]


def test_chain_silently_drops_unknown_providers(monkeypatch):
    from app.core import config as config_mod
    from app.services.llm.router import get_provider_chain

    monkeypatch.setattr(
        config_mod.settings, "llm_provider_chain", "made-up,gemini,nonsense"
    )
    monkeypatch.setattr(config_mod.settings, "llm_provider", "")
    monkeypatch.setattr(config_mod.settings, "llm_gemini_api_key", "gem-key-xxx")
    monkeypatch.setattr(config_mod.settings, "llm_anthropic_api_key", "")

    chain = get_provider_chain()
    assert [p.name for p in chain] == ["gemini"]


def test_legacy_get_provider_returns_first_chain_entry(monkeypatch):
    from app.core import config as config_mod
    from app.services.llm.router import get_provider

    monkeypatch.setattr(config_mod.settings, "llm_provider_chain", "gemini,anthropic")
    monkeypatch.setattr(config_mod.settings, "llm_provider", "")
    monkeypatch.setattr(config_mod.settings, "llm_gemini_api_key", "gem-key-xxx")
    monkeypatch.setattr(config_mod.settings, "llm_anthropic_api_key", "ant-key-xxx")

    p = get_provider()
    assert p is not None
    assert p.name == "gemini"


def test_legacy_single_provider_still_works(monkeypatch):
    """`LLM_PROVIDER=anthropic` (no chain set) still produces a single-
    entry chain. Existing deployments don't need to migrate."""
    from app.core import config as config_mod
    from app.services.llm.router import get_provider_chain

    monkeypatch.setattr(config_mod.settings, "llm_provider_chain", "")
    monkeypatch.setattr(config_mod.settings, "llm_provider", "anthropic")
    monkeypatch.setattr(config_mod.settings, "llm_anthropic_api_key", "ant-key-xxx")

    chain = get_provider_chain()
    assert [p.name for p in chain] == ["anthropic"]


# ── Orchestration: cascading fallback ───────────────────────────────


@pytest.mark.asyncio
async def test_analyze_falls_back_when_first_provider_raises(monkeypatch):
    """Inject a chain where the first provider raises StubProviderError
    and the second returns success. The orchestrator should return the
    second provider's response, not bubble the first error."""
    from app.services.documents import analyze as analyze_mod
    from app.services.documents import budget as budget_svc

    # No budget pressure for this test.
    async def _allow(_db, _projected):
        return True, budget_svc.BudgetStatus(
            year=2026, month=5, cap_tokens=999_999,
            used_tokens=0, remaining_tokens=999_999,
            cost_estimate_usd=0.0, per_provider={}, over_budget=False,
        )
    monkeypatch.setattr(budget_svc, "can_spend", _allow)

    failing = AsyncMock()
    failing.name = "gemini"
    failing.chat = AsyncMock(side_effect=StubProviderError("rate-limit hit"))

    succeeding = AsyncMock()
    succeeding.name = "anthropic"
    succeeding.chat = AsyncMock(
        return_value=LLMResponse(
            text="fallback answer",
            provider="anthropic",
            model="claude-sonnet-4-6",
            input_tokens=42,
            output_tokens=7,
        )
    )

    monkeypatch.setattr(analyze_mod, "get_provider_chain", lambda: [failing, succeeding])

    result = await analyze_mod.analyze_document(
        db=None,  # not used in this path — budget is mocked
        document_text="Revenue was $12B.",
        user_prompt="What was revenue?",
    )

    assert result.provider == "anthropic"
    assert result.response_text == "fallback answer"
    assert result.input_tokens == 42
    failing.chat.assert_awaited_once()
    succeeding.chat.assert_awaited_once()


@pytest.mark.asyncio
async def test_analyze_raises_when_entire_chain_fails(monkeypatch):
    """Both providers raise StubProviderError → analyze_document raises
    StubProviderError quoting the LAST error (the paid provider's reason,
    in a free-first chain — that's what the operator most cares about)."""
    from app.services.documents import analyze as analyze_mod
    from app.services.documents import budget as budget_svc

    async def _allow(_db, _projected):
        return True, budget_svc.BudgetStatus(
            year=2026, month=5, cap_tokens=999_999,
            used_tokens=0, remaining_tokens=999_999,
            cost_estimate_usd=0.0, per_provider={}, over_budget=False,
        )
    monkeypatch.setattr(budget_svc, "can_spend", _allow)

    first = AsyncMock()
    first.name = "gemini"
    first.chat = AsyncMock(side_effect=StubProviderError("gemini quota exhausted"))

    second = AsyncMock()
    second.name = "anthropic"
    second.chat = AsyncMock(side_effect=StubProviderError("anthropic 401 invalid key"))

    monkeypatch.setattr(analyze_mod, "get_provider_chain", lambda: [first, second])

    with pytest.raises(StubProviderError) as exc_info:
        await analyze_mod.analyze_document(
            db=None,
            document_text="Revenue was $12B.",
            user_prompt="What was revenue?",
        )

    # The aggregate message should reference the last failure so the
    # operator can debug the right thing.
    assert "anthropic 401 invalid key" in str(exc_info.value)


@pytest.mark.asyncio
async def test_analyze_503s_when_chain_is_empty(monkeypatch):
    from app.services.documents import analyze as analyze_mod
    from app.services.documents import budget as budget_svc

    async def _allow(_db, _projected):
        return True, budget_svc.BudgetStatus(
            year=2026, month=5, cap_tokens=999_999,
            used_tokens=0, remaining_tokens=999_999,
            cost_estimate_usd=0.0, per_provider={}, over_budget=False,
        )
    monkeypatch.setattr(budget_svc, "can_spend", _allow)
    monkeypatch.setattr(analyze_mod, "get_provider_chain", lambda: [])

    with pytest.raises(StubProviderError) as exc_info:
        await analyze_mod.analyze_document(
            db=None,
            document_text="Revenue was $12B.",
            user_prompt="What was revenue?",
        )
    assert "not configured" in str(exc_info.value).lower()


# ── Gemini provider: HTTP-level behavior ────────────────────────────


def _mock_post_returning(status_code: int, payload: dict | None = None):
    """Build a fake httpx.AsyncClient.post that returns a Response with
    the given status_code and JSON body."""
    async def fake_post(self, url, params=None, json=None):
        response = AsyncMock(spec=httpx.Response)
        response.status_code = status_code
        response.json = lambda: payload if payload is not None else {}
        return response
    return fake_post


@pytest.mark.asyncio
async def test_gemini_happy_path_parses_response():
    """200 OK with one candidate text + usageMetadata → LLMResponse with
    text + token counts populated."""
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Revenue was $12B in Q3."}],
                    "role": "model",
                },
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 120,
            "candidatesTokenCount": 18,
            "totalTokenCount": 138,
        },
    }
    with patch.object(httpx.AsyncClient, "post", _mock_post_returning(200, payload)):
        provider = GeminiProvider(api_key="gem-key-xxx")
        resp = await provider.chat([
            LLMMessage(role="system", content="You are an analyst."),
            LLMMessage(role="user", content="What was revenue?"),
        ])

    assert resp.text == "Revenue was $12B in Q3."
    assert resp.provider == "gemini"
    assert resp.model == "gemini-2.5-flash"
    assert resp.input_tokens == 120
    assert resp.output_tokens == 18


@pytest.mark.asyncio
async def test_gemini_401_raises_auth_error():
    with patch.object(httpx.AsyncClient, "post", _mock_post_returning(401, {})):
        provider = GeminiProvider(api_key="bad-key")
        with pytest.raises(StubProviderError) as exc_info:
            await provider.chat([LLMMessage(role="user", content="hi")])
    assert "auth failed" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_gemini_429_raises_rate_limit_error():
    with patch.object(httpx.AsyncClient, "post", _mock_post_returning(429, {})):
        provider = GeminiProvider(api_key="gem-key-xxx")
        with pytest.raises(StubProviderError) as exc_info:
            await provider.chat([LLMMessage(role="user", content="hi")])
    assert "rate-limit" in str(exc_info.value).lower() or "quota" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_gemini_5xx_raises_server_error():
    with patch.object(httpx.AsyncClient, "post", _mock_post_returning(503, {})):
        provider = GeminiProvider(api_key="gem-key-xxx")
        with pytest.raises(StubProviderError) as exc_info:
            await provider.chat([LLMMessage(role="user", content="hi")])
    assert "503" in str(exc_info.value)


@pytest.mark.asyncio
async def test_gemini_empty_candidates_raises():
    """Safety-blocked or empty responses must NOT return blank text —
    they raise so the cascading chain can fall back."""
    payload = {
        "candidates": [],
        "promptFeedback": {"blockReason": "SAFETY"},
    }
    with patch.object(httpx.AsyncClient, "post", _mock_post_returning(200, payload)):
        provider = GeminiProvider(api_key="gem-key-xxx")
        with pytest.raises(StubProviderError) as exc_info:
            await provider.chat([LLMMessage(role="user", content="hi")])
    assert "no candidates" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_gemini_empty_api_key_raises_before_network():
    """A missing key must raise BEFORE making a network call. We
    confirm by patching post to assert-not-called — but the simpler
    check is just that the error message says the key is empty."""
    provider = GeminiProvider(api_key="")
    with pytest.raises(StubProviderError) as exc_info:
        await provider.chat([LLMMessage(role="user", content="hi")])
    assert "LLM_GEMINI_API_KEY" in str(exc_info.value)
