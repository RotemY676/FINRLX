"""Stooq market-data adapter (Program LEAP F1).

Second leg of the price provider chain (D1: yfinance -> stooq -> cache).
Stooq serves daily OHLCV as CSV over HTTPS with no API key, which makes it
a suitable independent fallback when Yahoo endpoints rate-limit or break.

Contract: identical to yfinance_provider.fetch_bars —
    fetch_bars(ticker, asset_id, start, end) -> (list[bar dict], warnings)
Bars that fail validation are excluded, with a warning per rejection.

Notes:
- US listings on Stooq use a `.us` suffix (AAPL -> aapl.us). Tickers that
  already contain a dot (e.g. BRK.B -> brk-b.us per Stooq convention) are
  normalized. Non-US suffixed tickers are passed through lowercased.
- Stooq CSV columns: Date,Open,High,Low,Close,Volume. Missing volume rows
  are rejected by validation like any other malformed bar.
- Network access is via urllib (stdlib) — no new dependency (D21).
"""
from __future__ import annotations

import csv
import io
import logging
import urllib.error
import urllib.request
from datetime import date, datetime
from typing import Any

from app.models.base import gen_uuid
from app.services.data_providers.validation import (
    detect_gaps,
    detect_stale_ticks,
    validate_bar,
)

logger = logging.getLogger(__name__)

PROVIDER_NAME = "stooq"
_BASE_URL = "https://stooq.com/q/d/l/"
_TIMEOUT_SECONDS = 15

__all__ = ["PROVIDER_NAME", "fetch_bars", "stooq_symbol"]


def stooq_symbol(ticker: str) -> str:
    """Map an exchange ticker to Stooq's symbol convention."""
    t = ticker.strip().lower()
    if "." in t:
        base, suffix = t.rsplit(".", 1)
        # Foreign-exchange suffixes Stooq knows natively (e.g. .de, .uk, .jp)
        if len(suffix) == 2 and suffix.isalpha() and suffix != "us":
            return t
        # US share classes: BRK.B -> brk-b.us
        return f"{base}-{suffix}.us"
    return f"{t}.us"


def _http_get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "FINRLX/1.0"})
    with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:  # noqa: S310 — https only
        return resp.read().decode("utf-8", errors="replace")


def fetch_bars(
    ticker: str,
    asset_id: str,
    start: date,
    end: date,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Fetch daily OHLCV bars from Stooq for [start, end] inclusive."""
    warnings: list[str] = []
    url = (
        f"{_BASE_URL}?s={stooq_symbol(ticker)}"
        f"&d1={start.strftime('%Y%m%d')}&d2={end.strftime('%Y%m%d')}&i=d"
    )
    try:
        body = _http_get(url)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        logger.warning("stooq fetch failed for %s: %s", ticker, exc)
        return [], [f"stooq fetch failed for {ticker}: {exc!s}"]

    stripped = body.strip()
    if not stripped or stripped.lower().startswith(("no data", "<html")):
        return [], [f"stooq returned no data for {ticker} in [{start}, {end}]"]

    bars: list[dict[str, Any]] = []
    reader = csv.DictReader(io.StringIO(stripped))
    if not reader.fieldnames or "Date" not in reader.fieldnames:
        return [], [f"stooq returned malformed CSV for {ticker} (header: {reader.fieldnames})"]

    for row in reader:
        try:
            bar_date = datetime.strptime(row["Date"], "%Y-%m-%d").date()
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
                "volume": int(float(row.get("Volume") or 0)),
                "source": PROVIDER_NAME,
            }
        except (KeyError, TypeError, ValueError) as exc:
            warnings.append(f"{ticker} malformed stooq row {row.get('Date', '?')}: {exc!s}")
            continue
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
