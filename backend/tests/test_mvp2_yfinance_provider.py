"""Phase MVP-2 — yfinance market-data provider tests.

Covers:
- Data quality validators (OHLC inversion, negative volume, zero values, missing fields)
- Gap detection across weekday calendar
- Stale-tick detection (consecutive identical OHLCV days)
- Provider router dispatches correctly (yfinance / local / unknown fallback)
- Mocked yfinance happy path: bars normalized into MarketBar-shape dicts
- Mocked yfinance failure path: empty DataFrame -> warnings, no rows
- Mocked yfinance exception path: connection error -> warnings, no rows

All yfinance calls are MOCKED — CI never hits Yahoo.
"""
from __future__ import annotations

from datetime import date
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from app.services.data_providers import yfinance_provider as yf_p
from app.services.ingest import _fetch_bars_by_provider


# ---------- helpers -------------------------------------------------------


def _bar(d, o=100.0, h=101.0, l=99.0, c=100.5, v=1_000_000):
    return {
        "id": "x",
        "asset_id": "asset-1",
        "ticker": "TST",
        "bar_date": d,
        "interval": "1d",
        "open": o,
        "high": h,
        "low": l,
        "close": c,
        "volume": v,
        "source": "yfinance",
    }


def _df(records: list[tuple[date, float, float, float, float, int]]) -> pd.DataFrame:
    idx = pd.DatetimeIndex([pd.Timestamp(d) for d, *_ in records])
    return pd.DataFrame(
        {
            "Open": [o for _, o, *_ in records],
            "High": [h for _, _, h, *_ in records],
            "Low": [l for _, _, _, l, *_ in records],
            "Close": [c for _, _, _, _, c, _ in records],
            "Volume": [v for _, _, _, _, _, v in records],
        },
        index=idx,
    )


# ---------- _validate_bar -------------------------------------------------


def test_validate_bar_clean_returns_no_warnings():
    assert yf_p._validate_bar(_bar(date(2026, 5, 19))) == []


def test_validate_bar_flags_open_outside_lh():
    w = yf_p._validate_bar(_bar(date(2026, 5, 19), o=110, h=101, l=99, c=100))
    assert any("open" in msg for msg in w)


def test_validate_bar_flags_close_outside_lh():
    w = yf_p._validate_bar(_bar(date(2026, 5, 19), o=100, h=101, l=99, c=110))
    assert any("close" in msg for msg in w)


def test_validate_bar_flags_low_above_high():
    w = yf_p._validate_bar(_bar(date(2026, 5, 19), o=100, h=99, l=101, c=100))
    # The bar fails both open/close outside-LH and low>high checks.
    assert any("low" in msg and "high" in msg for msg in w)


def test_validate_bar_flags_negative_volume():
    w = yf_p._validate_bar(_bar(date(2026, 5, 19), v=-1))
    assert any("volume" in msg for msg in w)


def test_validate_bar_flags_zero_price():
    w = yf_p._validate_bar(_bar(date(2026, 5, 19), o=0, h=0, l=0, c=0))
    assert any("non-positive" in msg for msg in w)


# ---------- gap detection -------------------------------------------------


def test_detect_gaps_returns_empty_for_consecutive_weekdays():
    bars = [_bar(date(2026, 5, 18)), _bar(date(2026, 5, 19)), _bar(date(2026, 5, 20))]
    assert yf_p.detect_gaps(bars) == []


def test_detect_gaps_flags_missing_midweek_day():
    # 2026-05-18 = Mon, 2026-05-20 = Wed. Missing Tue 2026-05-19.
    bars = [_bar(date(2026, 5, 18)), _bar(date(2026, 5, 20))]
    gaps = yf_p.detect_gaps(bars)
    assert "2026-05-19" in gaps


def test_detect_gaps_ignores_weekend():
    # Fri 2026-05-15, Mon 2026-05-18 — weekend ignored.
    bars = [_bar(date(2026, 5, 15)), _bar(date(2026, 5, 18))]
    assert yf_p.detect_gaps(bars) == []


# ---------- stale tick detection ------------------------------------------


def test_detect_stale_ticks_returns_empty_for_varying_bars():
    bars = [_bar(date(2026, 5, 18), c=100), _bar(date(2026, 5, 19), c=101)]
    assert yf_p.detect_stale_ticks(bars) == []


def test_detect_stale_ticks_flags_exact_duplicate_ohlcv():
    bars = [_bar(date(2026, 5, 18)), _bar(date(2026, 5, 19))]  # identical
    stale = yf_p.detect_stale_ticks(bars)
    assert "2026-05-19" in stale


# ---------- fetch_bars happy path ----------------------------------------


@pytest.mark.asyncio
async def test_fetch_bars_happy_path_normalizes_dataframe_to_market_bar_shape():
    df = _df([
        (date(2026, 5, 18), 100.0, 102.0, 99.5, 101.5, 10_000_000),
        (date(2026, 5, 19), 101.0, 103.0, 100.0, 102.5, 11_000_000),
    ])
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = df
    with patch.object(yf_p, "_import_yfinance") as mock_imp:
        mock_yf_module = MagicMock()
        mock_yf_module.Ticker.return_value = mock_ticker
        mock_imp.return_value = mock_yf_module
        bars, warnings = yf_p.fetch_bars("TST", "asset-1", date(2026, 5, 18), date(2026, 5, 19))
    assert len(bars) == 2
    assert all(b["source"] == "yfinance" for b in bars)
    assert all(b["interval"] == "1d" for b in bars)
    assert bars[0]["open"] == 100.0
    assert bars[0]["volume"] == 10_000_000
    assert warnings == []


@pytest.mark.asyncio
async def test_fetch_bars_invalid_dataframe_row_is_excluded_with_warning():
    # Include one row with high<low — must be excluded with a warning.
    df = _df([
        (date(2026, 5, 18), 100.0, 102.0, 99.5, 101.5, 10_000_000),
        (date(2026, 5, 19), 100.0, 95.0, 110.0, 101.0, 10_000_000),  # high<low
    ])
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = df
    with patch.object(yf_p, "_import_yfinance") as mock_imp:
        mock_yf_module = MagicMock()
        mock_yf_module.Ticker.return_value = mock_ticker
        mock_imp.return_value = mock_yf_module
        bars, warnings = yf_p.fetch_bars("TST", "asset-1", date(2026, 5, 18), date(2026, 5, 19))
    assert len(bars) == 1
    assert any("2026-05-19" in w for w in warnings)


@pytest.mark.asyncio
async def test_fetch_bars_empty_dataframe_yields_warning_no_rows():
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = pd.DataFrame()
    with patch.object(yf_p, "_import_yfinance") as mock_imp:
        mock_yf_module = MagicMock()
        mock_yf_module.Ticker.return_value = mock_ticker
        mock_imp.return_value = mock_yf_module
        bars, warnings = yf_p.fetch_bars("DELISTED", "asset-x", date(2026, 5, 18), date(2026, 5, 19))
    assert bars == []
    assert len(warnings) == 1
    assert "no data" in warnings[0]


@pytest.mark.asyncio
async def test_fetch_bars_exception_yields_warning_no_rows():
    mock_ticker = MagicMock()
    mock_ticker.history.side_effect = ConnectionError("Yahoo unreachable")
    with patch.object(yf_p, "_import_yfinance") as mock_imp:
        mock_yf_module = MagicMock()
        mock_yf_module.Ticker.return_value = mock_ticker
        mock_imp.return_value = mock_yf_module
        bars, warnings = yf_p.fetch_bars("AAPL", "asset-1", date(2026, 5, 18), date(2026, 5, 19))
    assert bars == []
    assert any("yfinance fetch failed" in w for w in warnings)


# ---------- provider router ----------------------------------------------


@pytest.mark.asyncio
async def test_provider_router_dispatches_local_to_deterministic_generator():
    bars, warnings = _fetch_bars_by_provider(
        "local", "AAPL", "asset-aapl", date(2026, 5, 18), date(2026, 5, 22)
    )
    assert len(bars) == 5  # Mon-Fri inclusive
    assert all(b["source"] == "local" for b in bars)
    assert warnings == []


@pytest.mark.asyncio
async def test_provider_router_dispatches_yfinance_to_yfinance_provider():
    with patch.object(yf_p, "fetch_bars") as mock_fetch:
        mock_fetch.return_value = ([{"ticker": "TST"}], ["mocked warning"])
        bars, warnings = _fetch_bars_by_provider(
            "yfinance", "TST", "asset-1", date(2026, 5, 18), date(2026, 5, 19)
        )
        assert mock_fetch.called
        assert warnings == ["mocked warning"]


@pytest.mark.asyncio
async def test_provider_router_freeform_source_falls_through_to_local_silently():
    """Backward-compat: any source other than 'yfinance' routes to the local
    generator and uses the original string as the manifest label (no warning)."""
    bars, warnings = _fetch_bars_by_provider(
        "local-specific", "AAPL", "asset-aapl", date(2026, 5, 18), date(2026, 5, 18)
    )
    assert len(bars) == 1  # one weekday
    assert warnings == []
    # Source label is preserved (not rewritten to "local")
    assert bars[0]["source"] == "local-specific"
