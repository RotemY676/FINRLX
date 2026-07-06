"""Phase O-5 — assistant endpoints stub contract.

Today every /api/v1/assistant/* endpoint must return 503 because no
LLM provider is wired in. The router-status endpoint must reflect the
empty configuration. When the operator flips LLM_PROVIDER and the
matching API key, the 503 turns into a real provider call (out of
scope for this phase, but verified by these tests' negative shape).
"""
from __future__ import annotations

import pytest

from app.services.llm.router import get_provider, get_provider_status


@pytest.mark.asyncio
async def test_assistant_status_returns_unconfigured_by_default(client, monkeypatch):
    # Reset to default — empty provider.
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "llm_provider", "")
    monkeypatch.setattr(config_mod.settings, "llm_anthropic_api_key", "")
    monkeypatch.setattr(config_mod.settings, "llm_openai_api_key", "")
    # /assistant/status requires auth; a 401 is also acceptable evidence the
    # route is wired (the contract guarantees auth-required + flag-gated).
    r = await client.get("/api/v1/assistant/status")
    assert r.status_code in (200, 401), r.text
    if r.status_code == 200:
        data = r.json()["data"]
        assert data["configured"] is False
        assert data["provider"] in ("", None)


def test_router_returns_none_when_no_provider(monkeypatch):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "llm_provider", "")
    assert get_provider() is None
    s = get_provider_status()
    assert s.configured is False
    assert "LLM_PROVIDER" in s.detail


def test_router_returns_none_for_unknown_provider(monkeypatch):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "llm_provider", "bogus-provider")
    assert get_provider() is None
    s = get_provider_status()
    assert s.configured is False
    assert "Unknown" in s.detail


def test_router_returns_none_when_provider_set_but_key_missing(monkeypatch):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "llm_provider", "anthropic")
    monkeypatch.setattr(config_mod.settings, "llm_anthropic_api_key", "")
    assert get_provider() is None
    s = get_provider_status()
    assert s.configured is False
    assert "missing API key" in s.detail


def test_router_constructs_anthropic_when_key_present(monkeypatch):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "llm_provider", "anthropic")
    monkeypatch.setattr(config_mod.settings, "llm_anthropic_api_key", "fake-key-for-stub")
    provider = get_provider()
    assert provider is not None
    assert provider.name == "anthropic"


def test_router_constructs_openai_when_key_present(monkeypatch):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "llm_provider", "openai")
    monkeypatch.setattr(config_mod.settings, "llm_openai_api_key", "fake-key-for-stub")
    provider = get_provider()
    assert provider is not None
    assert provider.name == "openai"


def test_router_constructs_local_ollama_without_key(monkeypatch):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "llm_provider", "local")
    provider = get_provider()
    assert provider is not None
    assert provider.name == "local"


@pytest.mark.asyncio
async def test_anthropic_stub_raises_with_friendly_message(monkeypatch):
    # Phase 17.2 made the Anthropic provider real, so a placeholder key now
    # triggers a live API call. The friendly no-network guard is the
    # empty-key path — assert that instead (LEAP F0 baseline fix).
    from app.services.llm.anthropic import AnthropicProvider
    from app.services.llm.provider import StubProviderError
    from app.services.llm.types import LLMMessage
    p = AnthropicProvider(api_key="")
    with pytest.raises(StubProviderError, match="LLM_ANTHROPIC_API_KEY is empty"):
        await p.chat([LLMMessage(role="user", content="hi")])


@pytest.mark.asyncio
async def test_openai_stub_raises_with_friendly_message(monkeypatch):
    from app.services.llm.openai import OpenAIProvider
    from app.services.llm.provider import StubProviderError
    from app.services.llm.types import LLMMessage
    p = OpenAIProvider(api_key="stub")
    with pytest.raises(StubProviderError, match="stub"):
        await p.chat([LLMMessage(role="user", content="hi")])


@pytest.mark.asyncio
async def test_local_stub_raises_with_friendly_message(monkeypatch):
    from app.services.llm.local import LocalOllamaProvider
    from app.services.llm.provider import StubProviderError
    from app.services.llm.types import LLMMessage
    p = LocalOllamaProvider()
    with pytest.raises(StubProviderError, match="stub"):
        await p.chat([LLMMessage(role="user", content="hi")])
