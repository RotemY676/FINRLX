"""Stub fundamentals provider.

Default provider when `FUNDAMENTALS_PROVIDER` is unset. Returns a
structurally-complete envelope with every metric field `None` and a
`coverage_note` that explains why. The frontend handles this as an
honest "configure a provider" state, not as an error.

Why we return 200 instead of 503 here:
  - The frontend is more graceful when it can render the panel chrome
    (header + provenance footer + "configure provider" message) than
    when the whole request fails.
  - The endpoint layer can still 503 if you prefer; that decision lives
    in app.api.v1.research_fundamentals, not here.

When `app.api.v1.research_fundamentals` chooses 503 behaviour, this
provider exposes a `IS_STUB = True` flag so the endpoint can detect
it explicitly without an isinstance check.
"""
from __future__ import annotations

from datetime import UTC, datetime

from app.services.fundamentals.provider import FundamentalsProvider
from app.services.fundamentals.types import (
    FundamentalsResponse,
    PeersResponse,
)


_STUB_NOTE = (
    "No fundamentals provider configured. Set FUNDAMENTALS_PROVIDER=finnhub "
    "and FINNHUB_API_KEY=… in the backend environment to activate this surface."
)


class StubFundamentalsProvider(FundamentalsProvider):
    name: str = "stub"
    IS_STUB: bool = True

    async def get_fundamentals(self, ticker: str) -> FundamentalsResponse:
        return FundamentalsResponse(
            ticker=ticker.upper(),
            source="stub",
            cached_at=datetime.now(UTC).isoformat(),
            coverage_note=_STUB_NOTE,
        )

    async def get_peers(self, ticker: str) -> PeersResponse:
        return PeersResponse(
            target_ticker=ticker.upper(),
            peers=[],
            source="stub",
            cached_at=datetime.now(UTC).isoformat(),
            coverage_note=_STUB_NOTE,
        )
