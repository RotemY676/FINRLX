"""Provider router — picks a concrete LLM provider from settings.

The router is the only place application code touches a specific
provider class. Endpoints call `get_provider()` and either get a
working provider or `None` (in which case they should 503).
"""
from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.services.llm.anthropic import AnthropicProvider
from app.services.llm.local import LocalOllamaProvider
from app.services.llm.openai import OpenAIProvider
from app.services.llm.provider import LLMProvider


@dataclass
class ProviderStatus:
    configured: bool
    provider_name: str
    detail: str


_PROVIDER_FACTORIES = {
    "anthropic": lambda: (
        AnthropicProvider(
            api_key=settings.llm_anthropic_api_key,
            model=settings.llm_model or "claude-sonnet-4-6",
        )
        if settings.llm_anthropic_api_key
        else None
    ),
    "openai": lambda: (
        OpenAIProvider(
            api_key=settings.llm_openai_api_key,
            model=settings.llm_model or "gpt-4o-mini",
        )
        if settings.llm_openai_api_key
        else None
    ),
    "local": lambda: LocalOllamaProvider(
        base_url=settings.llm_local_base_url,
        model=settings.llm_model or "llama3.1:8b-instruct",
    ),
}


def get_provider() -> LLMProvider | None:
    """Return a configured provider, or None if not configured."""
    name = (settings.llm_provider or "").strip().lower()
    if not name:
        return None
    factory = _PROVIDER_FACTORIES.get(name)
    if factory is None:
        return None
    return factory()


def get_provider_status() -> ProviderStatus:
    """Describe the current provider configuration for diagnostics endpoints."""
    name = (settings.llm_provider or "").strip().lower()
    if not name:
        return ProviderStatus(
            configured=False,
            provider_name="",
            detail="LLM_PROVIDER is empty. Set LLM_PROVIDER=anthropic|openai|local and the matching API key to enable in-app assistant features.",
        )
    if name not in _PROVIDER_FACTORIES:
        return ProviderStatus(
            configured=False,
            provider_name=name,
            detail=f"Unknown LLM_PROVIDER value '{name}'. Allowed: anthropic, openai, local.",
        )
    provider = _PROVIDER_FACTORIES[name]()
    if provider is None:
        return ProviderStatus(
            configured=False,
            provider_name=name,
            detail=f"Provider '{name}' selected but missing API key. Set the matching env var.",
        )
    # Even a constructed provider here is a stub — see provider docstrings.
    return ProviderStatus(
        configured=True,
        provider_name=name,
        detail=f"Provider '{name}' selected. NOTE: current implementation is a stub; calling chat() will raise until the SDK call is wired in (see provider module docstring).",
    )
