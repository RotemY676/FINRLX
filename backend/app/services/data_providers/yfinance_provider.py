"""yfinance market-data adapter (Phase MVP-2).

This is the project's FIRST real data source. Replaces the deterministic
random-walk OHLCV with actual market data from Yahoo Finance.

Trade-offs accepted for MVP:
- yfinance is an unofficial Yahoo scraper; rate-limited; can break on Yahoo
  API changes. Acceptable because:
    * 5-15 beta testers
    * one daily fetch per ticker (~10-50 reqs/day total)
    * results cached in market_bars table (provider as source field)
- No survivorship-bias handling (delisted tickers): MVP-2 only ingests
  for tickers we explicitly request, which all exist today. Flagged for
  MVP-3 when provenance is added.

Replacement path: in MVP-2+ this module is the only thing to swap for
Alpha Vantage / Polygon / Tiingo — IngestService consumes the same
(list[dict], warnings) shape from any provider.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from app.models.base import gen_uuid
from app.services.data_providers.validation import (
    detect_gaps,
    detect_stale_ticks,
    validate_bar,
)

logger = logging.getLogger(__name__)

PROVIDER_NAME = "yfinance"

# Re-exported for backward compat with MVP-2 tests written against this module.
_validate_bar = validate_bar
__all__ = [
    "PROVIDER_NAME",
    "fetch_bars",
    "validate_bar",
    "detect_gaps",
    "detect_stale_ticks",
]


def _import_yfinance():
    """Lazy import so tests can mock without yfinance installed at module load."""
    import yfinance as yf
    return yf


# ── fetch ───────────────────────────────────────────────────────────────────


def fetch_bars(
    ticker: str,
    asset_id: str,
    start: date,
    end: date,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Fetch daily OHLCV bars from yfinance for [start, end] inclusive.

    Returns (bars, warnings). Bars that fail validation are excluded;
    each rejection adds to warnings.
    """
    warnings: list[str] = []
    try:
        yf = _import_yfinance()
    except ImportError:
        return [], [f"yfinance package not installed; cannot fetch {ticker}"]

    try:
        # yfinance end is exclusive — add a day so the requested end is included.
        tkr = yf.Ticker(ticker)
        df = tkr.history(
            start=start.isoformat(),
            end=(end + timedelta(days=1)).isoformat(),
            interval="1d",
            auto_adjust=False,
            actions=False,
        )
    except Exception as exc:  # noqa: BLE001 — provider boundary; never crash the pipeline
        logger.exception("yfinance fetch failed for %s", ticker)
        return [], [f"yfinance fetch failed for {ticker}: {exc!s}"]

    if df is None or df.empty:
        return [], [f"yfinance returned no data for {ticker} in [{start}, {end}]"]

    bars: list[dict[str, Any]] = []
    for ts, row in df.iterrows():
        bar_date = ts.date() if hasattr(ts, "date") else ts
        raw = {
            "id": gen_uuid(),
            "asset_id": asset_id,
            "ticker": ticker,
            "bar_date": bar_date,
            "interval": "1d",
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": int(row["Volume"]),
            "source": PROVIDER_NAME,
        }
        bar_warnings = validate_bar(raw)
        if bar_warnings:
            warnings.append(f"{ticker} {bar_date}: " + "; ".join(bar_warnings))
            continue
        bars.append(raw)

    if bars:
        gaps = detect_gaps(bars)
        if gaps:
            warnings.append(f"{ticker}: {len(gaps)} weekday gap(s) — first {gaps[:3]}")
        stale = detect_stale_ticks(bars)
        if stale:
            warnings.append(f"{ticker}: {len(stale)} stale-tick day(s) — {stale[:3]}")

    return bars, warnings
