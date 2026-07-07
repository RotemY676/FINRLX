"""Operation Credibility K1 — the one-price-truth contract.

Finding B of the credibility audit: production served a hash-seeded random
walk as a "price chart" alongside the real dossier price. These tests make
that class of defect structurally impossible to reintroduce:

  1. /pricechart closes must EXACTLY equal the dossier price_series closes
     for the same ticker and dates (both consume the same fetch_history).
  2. When the provider chain has nothing, /pricechart returns data=null —
     it never draws a curve.
  3. The module contains no random/synthetic generation whatsoever.
  4. Fabricated events are gone; the endpoint returns none.
"""
from __future__ import annotations

import pathlib
from datetime import date, timedelta

import pytest

from app.services.single_ticker_analysis import Bars


def _bars(n=420):
    dates, closes = [], []
    d, px, i = date(2024, 6, 3), 25.0, 0
    while len(dates) < n:
        if d.weekday() < 5:
            px *= 1.0 + (0.004 if (i // 20) % 2 == 0 else -0.002)
            dates.append(d); closes.append(round(px, 4)); i += 1
        d += timedelta(days=1)
    return Bars(dates=dates, closes=closes, volumes=[1_000_000] * n,
                highs=[c * 1.01 for c in closes], lows=[c * 0.99 for c in closes])


@pytest.mark.asyncio
async def test_pricechart_equals_dossier_prices(client, monkeypatch):
    import app.api.v1.pricechart as pc
    import app.services.data_providers.finnhub_extras as fx
    import app.services.data_providers.sec_xbrl as x
    import app.services.single_ticker_analysis as sta
    from app.services import autopilot

    bars = _bars()

    def fake_history(sym, days):
        if sym == "SPY":
            raise RuntimeError("no benchmark in this test")
        return bars

    monkeypatch.setattr(sta, "fetch_history", fake_history)
    monkeypatch.setattr(autopilot, "fetch_history", lambda s, d: bars)
    monkeypatch.setattr(autopilot, "fetch_news", lambda s, limit=20: ([], False))
    monkeypatch.setattr(x, "resolve_cik", lambda t: None)
    monkeypatch.setattr(fx, "_key", lambda: None)
    autopilot._dossier_cache.clear()
    pc._cache.clear()

    chart = (await client.get("/api/v1/pricechart?ticker=K1T")).json()["data"]
    dossier = (await client.get("/api/v1/autopilot/dossier?ticker=K1T")).json()["data"]

    chart_by_date = {p["date"]: p["price"] for p in chart["points"]}
    dossier_series = dossier["price_series"]
    overlap = [p for p in dossier_series if p["date"] in chart_by_date]
    assert len(overlap) >= 200, "surfaces must share the charted window"
    for p in overlap:
        assert chart_by_date[p["date"]] == pytest.approx(p["close"], abs=1e-6), (
            f"price divergence on {p['date']}: chart={chart_by_date[p['date']]} "
            f"dossier={p['close']}"
        )
    assert chart["events"] == []  # no invented headlines, ever


@pytest.mark.asyncio
async def test_pricechart_returns_null_not_fiction_when_chain_empty(client, monkeypatch):
    import app.api.v1.pricechart as pc
    import app.services.single_ticker_analysis as sta

    def no_data(sym, days):
        raise RuntimeError("providers down")

    monkeypatch.setattr(sta, "fetch_history", no_data)
    pc._cache.clear()
    body = (await client.get("/api/v1/pricechart?ticker=ZZZQ")).json()
    assert body["data"] is None


def test_pricechart_module_contains_no_synthetic_generation():
    src = pathlib.Path("app/api/v1/pricechart.py").read_text()
    for banned in ("random", "Random(", "_generate_series", "_synthetic",
                   "band_upper=", "drift", "ChartEvent(date="):
        assert banned not in src, f"synthetic-generation artifact found: {banned}"


# ── K1 Finding A: thin-provider resilience (the dash-wall fix) ──────────────


def test_fetch_history_falls_back_to_stooq_when_yfinance_thin(monkeypatch):
    """A thin yfinance window (real latest price, no depth) must NOT win over
    a deep stooq history — the exact production failure behind the dash-wall."""
    import app.services.single_ticker_analysis as sta

    deep = _bars(420)
    thin = Bars(dates=deep.dates[-5:], closes=deep.closes[-5:],
                volumes=deep.volumes[-5:], highs=deep.highs[-5:], lows=deep.lows[-5:])

    monkeypatch.setattr(sta, "_fetch_history_yfinance", lambda t, s, e: thin)
    monkeypatch.setattr(sta, "_bars_from_stooq", lambda t, s, e: deep)
    out = sta.fetch_history("UMC", 420)
    assert len(out.closes) == 420  # deepest coverage wins

    # and with depth restored, features actually populate (no dash-wall)
    from app.services.single_ticker_analysis import compute_features
    feats = compute_features(out.closes, out.volumes, [], False)
    assert feats["return_5d"][0] is not None
    assert feats["drawdown_20d"][0] is not None


def test_fetch_history_accepts_healthy_yfinance_without_fallback(monkeypatch):
    import app.services.single_ticker_analysis as sta

    deep = _bars(420)
    called = {"stooq": False}

    def no_stooq(t, s, e):
        called["stooq"] = True
        return Bars([], [], [], [], [])

    monkeypatch.setattr(sta, "_fetch_history_yfinance", lambda t, s, e: deep)
    monkeypatch.setattr(sta, "_bars_from_stooq", no_stooq)
    out = sta.fetch_history("NVDA", 420)
    assert len(out.closes) == 420 and called["stooq"] is False


def test_fetch_history_raises_only_when_all_sources_empty(monkeypatch):
    import app.services.single_ticker_analysis as sta

    monkeypatch.setattr(sta, "_fetch_history_yfinance",
                        lambda t, s, e: (_ for _ in ()).throw(RuntimeError("down")))
    monkeypatch.setattr(sta, "_bars_from_stooq", lambda t, s, e: Bars([], [], [], [], []))
    with pytest.raises(RuntimeError, match="no provider returned usable history"):
        sta.fetch_history("ZZZQ", 420)


def test_chain_prefers_deep_provider_over_thin_first_leg(monkeypatch):
    from datetime import date as _date
    from datetime import timedelta as _td

    from app.services.data_providers import chain_provider as cp

    thin_rows = [{"ticker": "UMC", "bar_date": _date(2026, 7, i + 1), "close": 10.0 + i,
                  "high": 11.0, "low": 9.0, "open": 10.0, "volume": 100} for i in range(3)]
    deep_rows = [{"ticker": "UMC", "bar_date": _date(2025, 1, 1) + _td(days=i), "close": 9.0,
                  "high": 9.5, "low": 8.5, "open": 9.0, "volume": 100} for i in range(300)]

    class ThinMod:
        @staticmethod
        def fetch_bars(t, a, s, e):
            return list(thin_rows), ["thin leg partial"]

    class DeepMod:
        @staticmethod
        def fetch_bars(t, a, s, e):
            return list(deep_rows), []

    monkeypatch.setattr(cp, "_CHAIN", [("thin", ThinMod), ("deep", DeepMod)])
    bars, warnings, served = cp.fetch_bars_chain(
        "UMC", "a1", _date(2025, 1, 1), _date(2026, 7, 6)
    )
    assert served == "deep" and len(bars) == 300
    assert any("PARTIAL" in w or "served by deep" in w for w in warnings)


@pytest.mark.asyncio
async def test_data_health_names_the_dash_wall(client, monkeypatch):
    """The diagnostic must expose a thin-source situation explicitly."""
    import app.services.single_ticker_analysis as sta

    deep = _bars(420)
    thin = Bars(dates=deep.dates[-5:], closes=deep.closes[-5:],
                volumes=deep.volumes[-5:], highs=deep.highs[-5:], lows=deep.lows[-5:])
    monkeypatch.setattr(sta, "_fetch_history_yfinance", lambda t, s, e: thin)
    monkeypatch.setattr(sta, "_bars_from_stooq", lambda t, s, e: deep)

    body = (await client.get("/api/v1/ops/data-health?tickers=UMC")).json()["data"]
    probe = body["probes"][0]
    assert probe["sources"]["yfinance"]["bars"] == 5      # thin source named
    assert probe["sources"]["stooq"]["bars"] == 420       # deep source named
    assert probe["served"]["bars"] == 420                 # resilient path serves depth
    assert probe["served"]["dash_wall"] is False
    assert probe["served"]["features_populated"].split("/")[0] != "0"
