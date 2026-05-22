"""Provider router — picks a concrete fundamentals provider from settings.

Mirrors app.services.llm.router. Endpoints call `get_provider()`. They
either get a working provider or `None`, in which case they 503 the
client with a structured detail.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.services.fundamentals.finnhub_provider import FinnhubFundamentalsProvider
from app.services.fundamentals.provider import FundamentalsProvider
from app.services.fundamentals.stub_provider import StubFundamentalsProvider


@dataclass
class ProviderStatus:
    configured: bool
    provider_name: str
    detail: str


_PROVIDER_FACTORIES: dict[str, callable] = {
    # The stub is selectable explicitly so the operator can pin it during
    # development without leaving FUNDAMENTALS_PROVIDER empty.
    "stub": lambda: StubFundamentalsProvider(),
    "finnhub": lambda: (
        FinnhubFundamentalsProvider(api_key=settings.fundamentals_finnhub_api_key)
        if settings.fundamentals_finnhub_api_key
        else None
    ),
}


def get_provider() -> FundamentalsProvider | None:
    """Return a configured provider, or None if not configured.

    Empty FUNDAMENTALS_PROVIDER returns the stub provider (rather than
    None) so the /research/fundamentals/{ticker} endpoint can always
    respond with a structurally-complete payload. The frontend treats
    `source == "stub"` + `coverage_note` as the activation-required
    state.
    """
    name = (settings.fundamentals_provider or "").strip().lower()
    if not name:
        return StubFundamentalsProvider()
    factory = _PROVIDER_FACTORIES.get(name)
    if factory is None:
        # Unknown provider name — fall back to the stub so the API
        # surface stays usable; status endpoint reports the misconfig.
        return StubFundamentalsProvider()
    provider = factory()
    if provider is None:
        # Selected provider has no key; fall back to the stub.
        return StubFundamentalsProvider()
    return provider


def get_provider_status() -> ProviderStatus:
    """Describe the current configuration for diagnostics endpoints."""
    name = (settings.fundamentals_provider or "").strip().lower()
    if not name:
        return ProviderStatus(
            configured=False,
            provider_name="stub",
            detail=(
                "FUNDAMENTALS_PROVIDER is empty. Set FUNDAMENTALS_PROVIDER=finnhub "
                "and FINNHUB_API_KEY=... in the backend env to enable real "
                "fundamentals + sector peers. Endpoint currently returns a stub "
                "envelope with all metrics None."
            ),
        )
    if name not in _PROVIDER_FACTORIES:
        return ProviderStatus(
            configured=False,
            provider_name=name,
            detail=(
                f"Unknown FUNDAMENTALS_PROVIDER value '{name}'. "
                f"Allowed: {sorted(_PROVIDER_FACTORIES.keys())}. "
                "Falling back to stub."
            ),
        )
    if name == "stub":
        return ProviderStatus(
            configured=True,
            provider_name="stub",
            detail="Stub provider selected explicitly. No real metrics returned.",
        )
    # finnhub (only real provider for now)
    if not settings.fundamentals_finnhub_api_key:
        return ProviderStatus(
            configured=False,
            provider_name=name,
            detail=(
                "Finnhub provider selected but FINNHUB_API_KEY is empty. "
                "Sign up at https://finnhub.io/ (free tier: 60 calls/min) and "
                "set FINNHUB_API_KEY in the backend env."
            ),
        )
    return ProviderStatus(
        configured=True,
        provider_name=name,
        detail=(
            "Finnhub provider selected. NOTE: Phase 16.0 ships a shim that "
            "returns the stub payload tagged source='finnhub'. Real HTTP "
            "implementation lands in Phase 16.2."
        ),
    )
