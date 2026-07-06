"""Program LEAP F1 — provider chain tests (gate G1.1).

Covers: stooq symbol normalization, stooq CSV parsing (happy path, empty,
malformed), and chain resolution order including forced failure of leg 1
and of both legs. All network I/O is mocked; no live calls.
"""
from __future__ import annotations

from datetime import date
from unittest import mock

from app.services.data_providers import chain_provider, stooq_provider

START = date(2026, 6, 1)
END = date(2026, 6, 5)

STOOQ_CSV = (
    "Date,Open,High,Low,Close,Volume\n"
    "2026-06-01,100.0,101.5,99.5,101.0,1200000\n"
    "2026-06-02,101.0,102.0,100.0,101.8,1100000\n"
    "2026-06-03,101.8,103.0,101.0,102.5,1300000\n"
)


def _bar(d: str, close: float) -> dict:
    return {
        "id": f"fixture-{d}",
        "asset_id": "asset-1",
        "ticker": "AAPL",
        "bar_date": date.fromisoformat(d),
        "interval": "1d",
        "open": close - 0.5,
        "high": close + 0.5,
        "low": close - 1.0,
        "close": close,
        "volume": 1_000_000,
        "source": "yfinance",
    }


# ── stooq symbol normalization ──────────────────────────────────────────────


def test_stooq_symbol_plain_us_ticker():
    assert stooq_provider.stooq_symbol("AAPL") == "aapl.us"


def test_stooq_symbol_share_class():
    assert stooq_provider.stooq_symbol("BRK.B") == "brk-b.us"


def test_stooq_symbol_foreign_suffix_passthrough():
    assert stooq_provider.stooq_symbol("SAP.DE") == "sap.de"


# ── stooq fetch/parse ───────────────────────────────────────────────────────


def test_stooq_happy_path_parses_and_validates():
    with mock.patch.object(stooq_provider, "_http_get", return_value=STOOQ_CSV):
        bars, warnings = stooq_provider.fetch_bars("AAPL", "asset-1", START, END)
    assert len(bars) == 3
    assert all(b["source"] == "stooq" for b in bars)
    assert bars[0]["bar_date"] == date(2026, 6, 1)
    assert bars[2]["close"] == 102.5
    assert not any("malformed" in w for w in warnings)


def test_stooq_empty_response_yields_no_bars_and_warning():
    with mock.patch.object(stooq_provider, "_http_get", return_value="No data"):
        bars, warnings = stooq_provider.fetch_bars("ZZZZ", "asset-2", START, END)
    assert bars == []
    assert any("no data" in w.lower() for w in warnings)


def test_stooq_malformed_csv_is_rejected_not_raised():
    with mock.patch.object(stooq_provider, "_http_get", return_value="garbage,,,\n1,2"):
        bars, warnings = stooq_provider.fetch_bars("AAPL", "asset-1", START, END)
    assert bars == []
    assert any("malformed" in w.lower() for w in warnings)


def test_stooq_network_failure_is_a_warning_not_an_exception():
    with mock.patch.object(
        stooq_provider, "_http_get", side_effect=OSError("connection refused")
    ):
        bars, warnings = stooq_provider.fetch_bars("AAPL", "asset-1", START, END)
    assert bars == []
    assert any("fetch failed" in w for w in warnings)


def test_stooq_partial_bad_rows_are_skipped_with_warnings():
    csv_with_bad_row = STOOQ_CSV + "2026-06-04,not_a_number,1,1,1,1\n"
    with mock.patch.object(stooq_provider, "_http_get", return_value=csv_with_bad_row):
        bars, warnings = stooq_provider.fetch_bars("AAPL", "asset-1", START, END)
    assert len(bars) == 3
    assert any("malformed stooq row 2026-06-04" in w for w in warnings)


# ── chain resolution (G1.1) ─────────────────────────────────────────────────


def test_chain_position_1_serves_when_healthy():
    yf_bars = [_bar("2026-06-01", 101.0)]
    with mock.patch.object(
        chain_provider.yfinance_provider, "fetch_bars", return_value=(yf_bars, [])
    ) as yf, mock.patch.object(
        chain_provider.stooq_provider, "fetch_bars"
    ) as stq:
        bars, warnings, used = chain_provider.fetch_bars_chain("AAPL", "asset-1", START, END)
    assert used == "yfinance"
    assert bars == yf_bars
    stq.assert_not_called()
    assert any("served by yfinance (position 1)" in w for w in warnings)
    yf.assert_called_once()


def test_chain_falls_back_to_stooq_when_leg1_fails():
    with mock.patch.object(
        chain_provider.yfinance_provider,
        "fetch_bars",
        return_value=([], ["yfinance fetch failed for AAPL: 429"]),
    ), mock.patch.object(stooq_provider, "_http_get", return_value=STOOQ_CSV):
        bars, warnings, used = chain_provider.fetch_bars_chain("AAPL", "asset-1", START, END)
    assert used == "stooq"
    assert len(bars) == 3
    assert all(b["source"] == "stooq" for b in bars)
    assert any("429" in w for w in warnings)  # failed-leg story preserved
    assert any("served by stooq (position 2)" in w for w in warnings)


def test_chain_both_legs_down_returns_empty_with_stale_cache_note():
    with mock.patch.object(
        chain_provider.yfinance_provider, "fetch_bars", return_value=([], ["yf down"])
    ), mock.patch.object(
        chain_provider.stooq_provider, "fetch_bars", return_value=([], ["stooq down"])
    ):
        bars, warnings, used = chain_provider.fetch_bars_chain("AAPL", "asset-1", START, END)
    assert used is None
    assert bars == []
    assert any("cached bars remain authoritative" in w for w in warnings)
    assert any("yf down" in w for w in warnings) and any("stooq down" in w for w in warnings)
