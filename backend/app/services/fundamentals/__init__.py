"""Fundamentals provider abstraction (Phase 16.0).

Mirrors the Phase O-5 LLM provider pattern in app.services.llm: a
pluggable layer that lets the operator turn fundamentals + peers on
by setting one env var (`FUNDAMENTALS_PROVIDER`) and the matching
API key — without touching application code.

Today every provider ships as a stub (`stub_provider.StubFundamentalsProvider`).
The Finnhub implementation lands in Phase 16.2 alongside cache and
real-key validation. The router + endpoints are fully wired so the
activation flip in Phase 16.3 is just configuration.
"""
from app.services.fundamentals.router import get_provider, get_provider_status, ProviderStatus
from app.services.fundamentals.types import (
    FundamentalsResponse,
    PeersResponse,
    PeerEntry,
)
from app.services.fundamentals.provider import (
    FundamentalsProvider,
    FundamentalsProviderError,
    FundamentalsNotAvailable,
)

__all__ = [
    "get_provider",
    "get_provider_status",
    "ProviderStatus",
    "FundamentalsResponse",
    "PeersResponse",
    "PeerEntry",
    "FundamentalsProvider",
    "FundamentalsProviderError",
    "FundamentalsNotAvailable",
]
