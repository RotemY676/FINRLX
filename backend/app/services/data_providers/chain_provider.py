"""Price provider chain (Program LEAP F1, decision D1).

Resolution order: yfinance -> stooq. The third leg (last-good cache with
stale=true) is served by IngestService/watchdog semantics: when the chain
returns nothing, existing market_bars remain authoritative and freshness
surfaces mark them stale rather than deleting or fabricating data.

Contract mirrors the single-provider modules:
    fetch_bars_chain(ticker, asset_id, start, end)
        -> (bars, warnings, provider_used | None)

Provenance: every returned bar's `source` field names the provider that
actually served it; the chain also emits a structured warning line
`chain: served by <provider> (position N)` so ingest manifests record the
resolution path (D7 chain_position without a schema change; the additive
per-bar fetched_at/provenance columns are tracked as F1 remaining work).
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

from app.services.data_providers import stooq_provider, yfinance_provider

logger = logging.getLogger(__name__)

CHAIN_SOURCE = "chain"

_CHAIN: list[tuple[str, Any]] = [
    # Late-bound: fetch_bars is resolved off the module at call time so the
    # chain always sees the current attribute (test doubles included).
    (yfinance_provider.PROVIDER_NAME, yfinance_provider),
    (stooq_provider.PROVIDER_NAME, stooq_provider),
]

__all__ = ["CHAIN_SOURCE", "fetch_bars_chain"]


def fetch_bars_chain(
    ticker: str,
    asset_id: str,
    start: date,
    end: date,
) -> tuple[list[dict[str, Any]], list[str], str | None]:
    """Try each provider in order; first non-empty bar set wins.

    Never raises: provider modules already convert failures into
    ([], warnings). All accumulated warnings from failed legs are preserved
    so manifests show the full degradation story.
    """
    all_warnings: list[str] = []
    for position, (name, module) in enumerate(_CHAIN, start=1):
        bars, warnings = module.fetch_bars(ticker, asset_id, start, end)
        all_warnings.extend(warnings)
        if bars:
            all_warnings.append(f"chain: served by {name} (position {position})")
            if position > 1:
                logger.warning(
                    "price chain degraded for %s: position %d (%s) served after "
                    "earlier provider(s) failed",
                    ticker,
                    position,
                    name,
                )
            return bars, all_warnings, name
    all_warnings.append(
        f"chain: all providers empty for {ticker} [{start}..{end}]; "
        "existing cached bars remain authoritative (stale)"
    )
    return [], all_warnings, None
