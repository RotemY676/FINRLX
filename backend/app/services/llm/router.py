"""Provider router — picks a concrete LLM provider from settings.

Two modes:

  (1) Single-provider (legacy): `LLM_PROVIDER=anthropic` selects one
      provider. `get_provider()` returns it or None.

  (2) Cascading chain (Phase 17.4): `LLM_PROVIDER_CHAIN=gemini,anthropic`
      yields an ordered list of providers via `get_provider_chain()`.
      The analyze layer walks the chain, trying each in order, falling
      back to the next on StubProviderError. This is the recommended
      configuration once a free provider (gemini) is wired in alongside
      the paid one (anthropic) so the paid quota is reserved for
      genuine fallback cases.

`get_provider()` remains for backwards compatibility — it returns the
first available provider in the chain (or, in single-provider mode, the
single configured one).
"""
from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.services.llm.anthropic import AnthropicProvider
from app.services.llm.gemini import GeminiProvider
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
    "gemini": lambda: (
        GeminiProvider(
            api_key=settings.llm_gemini_api_key,
            model=settings.llm_model or "gemini-2.5-flash",
        )
        if settings.llm_gemini_api_key
        else None
    ),
    "local": lambda: LocalOllamaProvider(
        base_url=settings.llm_local_base_url,
        model=settings.llm_model or "llama3.1:8b-instruct",
    ),
}


_ALLOWED_PROVIDERS = tuple(_PROVIDER_FACTORIES.keys())


def _parse_chain(raw: str) -> list[str]:
    """Split a comma-separated chain string into a clean list of
    provider names. Drops empties + unknowns silently — the caller
    inspects `get_provider_status()` for diagnostics."""
    out: list[str] = []
    for piece in (raw or "").split(","):
        name = piece.strip().lower()
        if name and name in _PROVIDER_FACTORIES and name not in out:
            out.append(name)
    return out


def get_provider_chain() -> list[LLMProvider]:
    """Return the ordered list of configured providers per
    `LLM_PROVIDER_CHAIN` (preferred) or `LLM_PROVIDER` (fallback).

    Skips providers that the factory can't construct (missing API key,
    etc.) so the chain only contains providers we can actually attempt.
    Returns [] if nothing is configured — callers should 503 in that
    case."""
    if settings.llm_provider_chain:
        names = _parse_chain(settings.llm_provider_chain)
    elif settings.llm_provider:
        single = settings.llm_provider.strip().lower()
        names = [single] if single in _PROVIDER_FACTORIES else []
    else:
        names = []

    chain: list[LLMProvider] = []
    for name in names:
        factory = _PROVIDER_FACTORIES.get(name)
        if factory is None:
            continue
        provider = factory()
        if provider is not None:
            chain.append(provider)
    return chain


def get_provider() -> LLMProvider | None:
    """Return a configured provider, or None if not configured.

    Backwards-compatible: returns the FIRST configured provider in the
    chain. New code should call `get_provider_chain()` directly so the
    analyze layer can fall back on StubProviderError."""
    chain = get_provider_chain()
    return chain[0] if chain else None


def get_provider_status() -> ProviderStatus:
    """Describe the current provider configuration for diagnostics
    endpoints. Reports on whichever activation mode the operator picked
    (chain or single)."""
    if settings.llm_provider_chain:
        raw_names = [
            piece.strip().lower()
            for piece in settings.llm_provider_chain.split(",")
            if piece.strip()
        ]
        if not raw_names:
            return ProviderStatus(
                configured=False,
                provider_name="",
                detail="LLM_PROVIDER_CHAIN is empty after parsing. Set e.g. LLM_PROVIDER_CHAIN=gemini,anthropic.",
            )
        unknown = [n for n in raw_names if n not in _PROVIDER_FACTORIES]
        if unknown:
            return ProviderStatus(
                configured=False,
                provider_name=",".join(raw_names),
                detail=(
                    f"Unknown providers in LLM_PROVIDER_CHAIN: {unknown}. "
                    f"Allowed: {list(_ALLOWED_PROVIDERS)}."
                ),
            )
        chain = get_provider_chain()
        if not chain:
            return ProviderStatus(
                configured=False,
                provider_name=",".join(raw_names),
                detail=(
                    "LLM_PROVIDER_CHAIN is set but no provider in the chain "
                    "has its API key configured. Set the matching env var."
                ),
            )
        chain_desc = ",".join(p.name for p in chain)
        return ProviderStatus(
            configured=True,
            provider_name=chain_desc,
            detail=f"Provider chain active: {chain_desc} (tried in order, falling back on errors).",
        )

    name = (settings.llm_provider or "").strip().lower()
    if not name:
        return ProviderStatus(
            configured=False,
            provider_name="",
            detail=(
                "LLM_PROVIDER is empty. Set LLM_PROVIDER="
                f"{'|'.join(_ALLOWED_PROVIDERS)} and the matching API key, "
                "or set LLM_PROVIDER_CHAIN for cascading fallback."
            ),
        )
    if name not in _PROVIDER_FACTORIES:
        return ProviderStatus(
            configured=False,
            provider_name=name,
            detail=f"Unknown LLM_PROVIDER value '{name}'. Allowed: {list(_ALLOWED_PROVIDERS)}.",
        )
    provider = _PROVIDER_FACTORIES[name]()
    if provider is None:
        return ProviderStatus(
            configured=False,
            provider_name=name,
            detail=f"Provider '{name}' selected but missing API key. Set the matching env var.",
        )
    return ProviderStatus(
        configured=True,
        provider_name=name,
        detail=f"Provider '{name}' selected.",
    )
