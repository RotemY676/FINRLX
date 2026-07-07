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
from datetime import UTC, date, datetime
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
    # K1: coverage-aware acceptance. "First non-empty wins" let a provider
    # returning a handful of bars beat a fallback holding the full window
    # (credibility audit Finding A). A leg now stands alone only when it
    # covers enough of the requested window; otherwise deeper legs are
    # consulted and the deepest set is served.
    expected = max(int(((end - start).days) * 5 / 7 * 0.9), 1)
    best: tuple[int, int, str, list[dict[str, Any]]] | None = None
    all_warnings: list[str] = []
    for position, (name, module) in enumerate(_CHAIN, start=1):
        bars, warnings = module.fetch_bars(ticker, asset_id, start, end)
        all_warnings.extend(warnings)
        if bars and (best is None or len(bars) > best[0]):
            best = (len(bars), position, name, bars)
        if bars and len(bars) >= expected * 0.5:
            fetched_at = datetime.now(UTC)
            for bar in bars:
                bar["fetched_at"] = fetched_at
                bar["chain_position"] = position
            _apply_quality_flags(bars, all_warnings)
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
    if best is not None:
        _count, position, name, bars = best
        fetched_at = datetime.now(UTC)
        for bar in bars:
            bar["fetched_at"] = fetched_at
            bar["chain_position"] = position
        _apply_quality_flags(bars, all_warnings)
        all_warnings.append(
            f"chain: served by {name} (position {position}) with PARTIAL coverage "
            f"({_count} bars vs ~{expected} expected)"
        )
        return bars, all_warnings, name
    all_warnings.append(
        f"chain: all providers empty for {ticker} [{start}..{end}]; "
        "existing cached bars remain authoritative (stale)"
    )
    return [], all_warnings, None


# ── data quality (D8) ───────────────────────────────────────────────────────

SUSPECT_MOVE_THRESHOLD = 0.40  # |day-over-day close change| beyond this is flagged


def _apply_quality_flags(bars: list[dict[str, Any]], warnings: list[str]) -> None:
    """Flag (never silently drop) bars that fail D8 sanity rules.

    Flagged bars persist with quality_flag set; the feature layer excludes
    them, and ops surfaces show them. Providers already reject nonpositive
    prices via validate_bar; this adds the cross-bar checks.
    """
    ordered = sorted(bars, key=lambda b: b["bar_date"])
    seen_dates: set = set()
    prev_close: float | None = None
    for bar in ordered:
        if bar["bar_date"] in seen_dates:
            bar["quality_flag"] = "duplicate"
            warnings.append(f"quality: duplicate bar flagged {bar['ticker']} {bar['bar_date']}")
        seen_dates.add(bar["bar_date"])
        close = bar["close"]
        if close <= 0:
            bar["quality_flag"] = "nonpositive"
            warnings.append(f"quality: nonpositive close flagged {bar['ticker']} {bar['bar_date']}")
        elif prev_close and prev_close > 0:
            move = abs(close / prev_close - 1.0)
            if move > SUSPECT_MOVE_THRESHOLD:
                bar["quality_flag"] = "suspect_move"
                warnings.append(
                    f"quality: suspect move {move:.0%} flagged {bar['ticker']} {bar['bar_date']}"
                )
        if bar.get("quality_flag") != "suspect_move" or prev_close is None:
            prev_close = close
