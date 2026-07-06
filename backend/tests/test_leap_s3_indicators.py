"""Program LEAP — S3 indicator golden tests (G4.1), F1 flag, F2 rebalance calendar.

Golden values are hand-verified against reference implementations computed
independently (see inline derivations); they pin exact numeric behavior so
any change to indicator math fails loudly.
"""
from __future__ import annotations

from datetime import date
from unittest import mock

from app.services.backtesting import REBALANCE_MONTHLY, BacktestService
from app.services.features import (
    _compute_macd_hist,
    _compute_rsi_wilder,
    _compute_turbulence,
    _ema_series,
)

# ── EMA / MACD ───────────────────────────────────────────────────────────────


def test_ema_series_golden():
    # alpha = 2/4 = 0.5, seeded at 2.0:
    # [2.0, 0.5*4+0.5*2=3.0, 0.5*8+0.5*3=5.5]
    assert _ema_series([2.0, 4.0, 8.0], span=3) == [2.0, 3.0, 5.5]


def test_macd_insufficient_data():
    assert _compute_macd_hist([100.0] * 34) == (None, "insufficient_data")


def test_macd_flat_series_is_zero():
    value, quality = _compute_macd_hist([100.0] * 60)
    assert quality == "ok"
    assert value == 0.0


def test_macd_rising_series_is_positive_and_matches_reference():
    closes = [100.0 + i for i in range(60)]  # steady uptrend
    value, quality = _compute_macd_hist(closes)
    assert quality == "ok"
    # Reference (numpy-free recomputation of the same definition):
    ema12 = _ema_series(closes, 12)
    ema26 = _ema_series(closes, 26)
    macd = [a - b for a, b in zip(ema12, ema26)]
    signal = _ema_series(macd, 9)
    assert value == round(macd[-1] - signal[-1], 6)
    assert value > 0


# ── RSI (Wilder) ────────────────────────────────────────────────────────────


def test_rsi_insufficient_data():
    assert _compute_rsi_wilder([100.0] * 14) == (None, "insufficient_data")


def test_rsi_all_gains_is_100():
    closes = [100.0 + i for i in range(16)]
    assert _compute_rsi_wilder(closes) == (100.0, "ok")


def test_rsi_all_losses_is_0():
    closes = [100.0 - i for i in range(16)]
    value, quality = _compute_rsi_wilder(closes)
    assert quality == "ok"
    assert value == 0.0


def test_rsi_wilder_golden_alternating():
    # 15 closes alternating +2/-1 from 100 => 14 changes: 7 gains of 2, 7 losses of 1
    closes = [100.0]
    for i in range(14):
        closes.append(closes[-1] + (2.0 if i % 2 == 0 else -1.0))
    # avg_gain = 14/14 = 1.0? No: gains sum = 7*2 = 14 over period 14 => 1.0
    # avg_loss = 7*1/14 = 0.5 ; RS = 2 ; RSI = 100 - 100/3 = 66.6667
    assert _compute_rsi_wilder(closes) == (66.6667, "ok")


# ── Turbulence ──────────────────────────────────────────────────────────────


def test_turbulence_flat_window_insufficient():
    closes = [100.0] * 30
    assert _compute_turbulence(closes) == (None, "insufficient_data")  # zero variance


def test_turbulence_quiet_then_shock_is_large():
    # 20 tiny alternating returns then a 10% jump: z^2 must be enormous.
    closes = [100.0]
    for i in range(21):
        closes.append(closes[-1] * (1.0001 if i % 2 == 0 else 0.9999))
    closes.append(closes[-1] * 1.10)
    value, quality = _compute_turbulence(closes)
    assert quality == "ok"
    assert value > 1000.0


def test_turbulence_typical_move_is_small():
    closes = [100.0]
    for i in range(22):
        closes.append(closes[-1] * (1.001 if i % 2 == 0 else 0.999))
    value, quality = _compute_turbulence(closes)
    assert quality == "ok"
    assert value < 5.0


# ── F2: rebalance-date calendar (legacy default byte-identical; opt-in skips holidays)


def _svc() -> BacktestService:
    return BacktestService(db=mock.MagicMock())


def test_rebalance_default_matches_legacy_weekday_logic():
    svc = _svc()
    got = svc._generate_rebalance_dates(date(2026, 6, 29), date(2026, 7, 13), "weekly")
    # Legacy: start Mon 6/29; +7 -> Mon 7/6 (weekday, no holiday awareness); +7 -> Mon 7/13
    assert got == [date(2026, 6, 29), date(2026, 7, 6), date(2026, 7, 13)]


def test_rebalance_calendar_optin_skips_observed_holiday():
    svc = _svc()
    # Friday 2026-07-03 is a start that legacy accepts (weekday) but XNYS is closed.
    legacy = svc._generate_rebalance_dates(date(2026, 7, 3), date(2026, 7, 3), "weekly")
    cal = svc._generate_rebalance_dates(
        date(2026, 7, 3), date(2026, 7, 3), "weekly", use_trading_calendar=True
    )
    assert legacy == [date(2026, 7, 3)]
    assert cal == []


def test_rebalance_calendar_optin_snaps_over_long_weekend():
    svc = _svc()
    got = svc._generate_rebalance_dates(
        date(2026, 6, 29), date(2026, 7, 13), REBALANCE_MONTHLY, use_trading_calendar=True
    )
    assert got[0] == date(2026, 6, 29)
    assert len(got) == 1  # +30d lands past end after snapping


# ── F1: LEAP_PRICE_CHAIN transparent upgrade flag ───────────────────────────


def test_yfinance_source_routes_to_chain_when_flag_on():
    from app.core.config import settings
    from app.services import ingest as ingest_mod

    sentinel_bars = [{"ticker": "AAPL", "source": "stooq"}]
    with mock.patch.object(settings, "leap_price_chain", True), mock.patch.object(
        ingest_mod.chain_provider,
        "fetch_bars_chain",
        return_value=(sentinel_bars, ["chain: served by stooq (position 2)"], "stooq"),
    ) as chain_mock:
        bars, warnings = ingest_mod._fetch_bars_by_provider(
            "yfinance", "AAPL", "asset-1", date(2026, 6, 1), date(2026, 6, 5)
        )
    chain_mock.assert_called_once()
    assert bars == sentinel_bars
    assert any("served by stooq" in w for w in warnings)


def test_yfinance_source_stays_direct_when_flag_off():
    from app.core.config import settings
    from app.services import ingest as ingest_mod

    with mock.patch.object(settings, "leap_price_chain", False), mock.patch.object(
        ingest_mod.yfinance_provider, "fetch_bars", return_value=([], ["direct"])
    ) as yf_mock, mock.patch.object(ingest_mod.chain_provider, "fetch_bars_chain") as chain_mock:
        ingest_mod._fetch_bars_by_provider(
            "yfinance", "AAPL", "asset-1", date(2026, 6, 1), date(2026, 6, 5)
        )
    yf_mock.assert_called_once()
    chain_mock.assert_not_called()
