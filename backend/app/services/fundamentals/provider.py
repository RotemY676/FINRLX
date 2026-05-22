"""Abstract Fundamentals provider base class.

Mirrors app.services.llm.provider — every concrete provider implements
the same two async methods. Endpoints call the abstract type; the
router picks the concrete provider from settings.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.services.fundamentals.types import FundamentalsResponse, PeersResponse


class FundamentalsProvider(ABC):
    """Stable interface every concrete fundamentals provider implements."""

    name: str = "abstract"

    @abstractmethod
    async def get_fundamentals(self, ticker: str) -> FundamentalsResponse:
        """Return the fundamentals envelope for a single ticker.

        Implementations should never raise on "ticker not covered" — they
        should return a `FundamentalsResponse` with `coverage_note` set
        and most numeric fields `None`. Raising is reserved for the
        provider misbehaving (network, key invalid, schema drift).
        """
        raise NotImplementedError

    @abstractmethod
    async def get_peers(self, ticker: str) -> PeersResponse:
        """Return the peers envelope for a single ticker.

        Same coverage policy as `get_fundamentals`: return an empty peers
        list with a `coverage_note` when the provider has no peers for
        the symbol. Reserve raising for genuine provider failures.
        """
        raise NotImplementedError


class FundamentalsProviderError(RuntimeError):
    """Raised when a provider hits an unrecoverable error (network, auth,
    schema drift). Endpoints translate this to a 502 with the provider
    name in the detail; never expose API keys or internal URLs."""


class FundamentalsNotAvailable(RuntimeError):
    """Raised by the stub provider when no real provider is configured.
    The endpoint layer translates this to a 503 with structured detail —
    same pattern as the LLM provider stub."""
