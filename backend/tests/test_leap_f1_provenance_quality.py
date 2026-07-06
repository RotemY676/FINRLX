"""Program LEAP F1 — provenance + quality-flag tests (gates G1.2, D8)."""
from __future__ import annotations

from datetime import date, datetime
from unittest import mock

from app.services.data_providers import chain_provider

START = date(2026, 6, 1)
END = date(2026, 6, 10)


def _bar(d: str, close: float, ticker: str = "AAPL") -> dict:
    return {
        "id": f"fx-{d}",
        "asset_id": "asset-1",
        "ticker": ticker,
        "bar_date": date.fromisoformat(d),
        "interval": "1d",
        "open": close,
        "high": close * 1.01,
        "low": close * 0.99,
        "close": close,
        "volume": 1_000_000,
        "source": "yfinance",
    }


def _serve(bars):
    return mock.patch.object(
        chain_provider.yfinance_provider, "fetch_bars", return_value=(bars, [])
    )


def test_chain_stamps_fetched_at_and_position_on_every_bar():
    with _serve([_bar("2026-06-01", 100.0), _bar("2026-06-02", 101.0)]):
        bars, _w, used = chain_provider.fetch_bars_chain("AAPL", "asset-1", START, END)
    assert used == "yfinance"
    assert all(isinstance(b["fetched_at"], datetime) for b in bars)
    assert all(b["chain_position"] == 1 for b in bars)
    assert all(b.get("quality_flag") is None for b in bars)


def test_quality_flag_suspect_move_over_threshold():
    with _serve([_bar("2026-06-01", 100.0), _bar("2026-06-02", 150.0)]):
        bars, warnings, _u = chain_provider.fetch_bars_chain("AAPL", "asset-1", START, END)
    flagged = [b for b in bars if b.get("quality_flag") == "suspect_move"]
    assert len(flagged) == 1 and flagged[0]["bar_date"] == date(2026, 6, 2)
    assert any("suspect move" in w for w in warnings)


def test_quality_flag_ignores_moves_at_or_under_threshold():
    with _serve([_bar("2026-06-01", 100.0), _bar("2026-06-02", 139.0)]):
        bars, _w, _u = chain_provider.fetch_bars_chain("AAPL", "asset-1", START, END)
    assert all(b.get("quality_flag") is None for b in bars)


def test_quality_flag_duplicate_date():
    with _serve([_bar("2026-06-01", 100.0), _bar("2026-06-01", 100.5)]):
        bars, warnings, _u = chain_provider.fetch_bars_chain("AAPL", "asset-1", START, END)
    assert any(b.get("quality_flag") == "duplicate" for b in bars)
    assert any("duplicate bar flagged" in w for w in warnings)


def test_suspect_move_does_not_poison_baseline_for_next_bar():
    # 100 -> 150 (flagged) -> 101: the 101 bar compares against 100, not 150,
    # so a single bad print does not cascade flags onto good data.
    with _serve([_bar("2026-06-01", 100.0), _bar("2026-06-02", 150.0), _bar("2026-06-03", 101.0)]):
        bars, _w, _u = chain_provider.fetch_bars_chain("AAPL", "asset-1", START, END)
    by_date = {b["bar_date"]: b.get("quality_flag") for b in bars}
    assert by_date[date(2026, 6, 2)] == "suspect_move"
    assert by_date[date(2026, 6, 3)] is None
