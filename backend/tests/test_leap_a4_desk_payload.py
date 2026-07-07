"""LEAP A4 — desk payload gates (D46-D48 + D42 endpoints)."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.services import desk_payload as dp
from app.services.single_ticker_analysis import Bars


def _bars(n=420, seed_shift=0.0):
    dates, closes = [], []
    d, px, i = date(2024, 1, 1), 100.0 + seed_shift, 0
    while len(dates) < n:
        if d.weekday() < 5:
            px *= 1.0 + (0.004 if (i // 20) % 2 == 0 else -0.002)
            dates.append(d); closes.append(round(px, 4)); i += 1
        d += timedelta(days=1)
    return Bars(dates=dates, closes=closes, volumes=[1_000_000] * n,
                highs=[c * 1.01 for c in closes], lows=[c * 0.99 for c in closes])


def test_regime_bands_rule_parity_with_production_label():
    """D47: the band rule must equal autopilot.regime_label at every prefix."""
    from app.services.autopilot import regime_label

    bars = _bars(300)
    for i in (60, 120, 200, 299):
        prefix = Bars(dates=bars.dates[:i + 1], closes=bars.closes[:i + 1],
                      volumes=bars.volumes[:i + 1], highs=bars.highs[:i + 1],
                      lows=bars.lows[:i + 1])
        assert dp._regime_at(prefix.closes) == regime_label(prefix)["label"]


def test_regime_bands_are_contiguous_and_cover_window():
    bars = _bars(400)
    bands = dp.regime_band_series(bars, max_sessions=260)
    assert bands, "bands expected"
    assert bands[-1]["end"] == bars.dates[-1].isoformat()
    for prev, cur in zip(bands, bands[1:]):
        assert prev["label"] != cur["label"]  # compressed
        assert prev["end"] < cur["start"]


def test_signal_matrix_percentiles_and_sparklines():
    bars = _bars(420)
    from app.services.single_ticker_analysis import compute_features
    from app.services.autopilot import _flatten_features

    flat = _flatten_features(compute_features(bars.closes, bars.volumes, [], False))
    rows = dp.signal_matrix(bars, flat)
    by_key = {r["key"]: r for r in rows}
    r5 = by_key["return_5d"]
    assert 0.0 <= r5["percentile"] <= 1.0
    assert len(r5["sparkline"]) == dp.SPARKLINE_SESSIONS
    # passthrough rows keep engine inputs visible without fake stats
    assert "news_sentiment_7d" in by_key or len(rows) > 5
    # short history -> percentile omitted honestly
    short = _bars(200)
    flat2 = _flatten_features(compute_features(short.closes, short.volumes, [], False))
    r = {x["key"]: x for x in dp.signal_matrix(short, flat2)}["return_5d"]
    assert r["percentile"] is None and "insufficient history" in r["percentile_note"]


def test_event_markers_filtered_sorted_and_evidence_linked():
    filings = {"tone": {"available": True, "filed_date": "2026-02-01", "form": "10-K"}}
    insider = {"available": True, "series_12m": [
        {"year": 2026, "month": 5, "net_change": -1200, "mspr": -20.0}]}
    news = [{"date": "2026-06-30", "title": "Capacity expansion announced"}]
    reb = [date(2026, 6, 1), date(2025, 1, 1)]  # second is before chart_start
    markers = dp.event_markers("T", news, filings, insider, reb, chart_start="2026-01-01")
    assert [m["type"] for m in markers] == ["filing", "insider", "rebalance", "news"]
    assert all(m["evidence_ref"] for m in markers)
    assert all(m["date"] >= "2026-01-01" for m in markers)


def test_split_windows_shapes():
    dates = [date(2025, 1, 1) + timedelta(weeks=i) for i in range(90)]
    out = dp.split_windows(dates, [(40, 55), (55, 70)])
    assert out[0]["train"]["end"] < out[0]["validation"]["start"]
    assert out[1]["train"]["end"] == out[0]["validation"]["end"]


# ── D42 endpoint contract ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_desk_section_endpoints(client, monkeypatch):
    from app.services import autopilot
    import app.services.data_providers.sec_xbrl as x
    import app.services.data_providers.finnhub_extras as fx

    bars = _bars(420)
    monkeypatch.setattr(autopilot, "fetch_history", lambda s, days: bars)
    monkeypatch.setattr(autopilot, "fetch_news", lambda s, limit=20: ([], False))
    monkeypatch.setattr(x, "resolve_cik", lambda t: None)
    monkeypatch.setattr(fx, "_key", lambda: None)
    autopilot._dossier_cache.clear()

    r = await client.get("/api/v1/autopilot/desk/A4EP/chart")
    assert r.status_code == 200
    body = r.json()["data"]
    assert body["section"] == "chart"
    assert body["payload"]["regime_bands"]
    assert isinstance(body["payload"]["event_markers"], list)

    r2 = await client.get("/api/v1/autopilot/desk/A4EP/tournament")
    assert r2.status_code == 200
    assert r2.json()["data"]["payload"]["split_windows"]

    r3 = await client.get("/api/v1/autopilot/desk/A4EP/nope")
    assert r3.status_code == 404

    r4 = await client.get("/api/v1/autopilot/desk/@@@/header")
    assert r4.status_code == 400


@pytest.mark.asyncio
async def test_header_section_carries_open_alerts(client, monkeypatch):
    """LEAP A6: S8 material-change incidents surface on the desk header."""
    from app.services import autopilot
    import app.services.data_providers.sec_xbrl as x
    import app.services.data_providers.finnhub_extras as fx
    from tests.conftest import test_session_factory as async_session_maker
    from app.models.ops import Incident
    from app.services.autopilot_refresh import INCIDENT_TITLE_PREFIX

    bars = _bars(420)
    monkeypatch.setattr(autopilot, "fetch_history", lambda s, days: bars)
    monkeypatch.setattr(autopilot, "fetch_news", lambda s, limit=20: ([], False))
    monkeypatch.setattr(x, "resolve_cik", lambda t: None)
    monkeypatch.setattr(fx, "_key", lambda: None)
    autopilot._dossier_cache.clear()

    async with async_session_maker() as db:
        db.add(Incident(
            title=f"{INCIDENT_TITLE_PREFIX}A6AL",
            severity=3, status="open",
            description="stance changed hold -> trim (evidence: /api/v1/autopilot/dossier?ticker=A6AL)",
        ))
        await db.commit()

    r = await client.get("/api/v1/autopilot/desk/A6AL/header")
    assert r.status_code == 200
    alerts = r.json()["data"]["payload"]["alerts"]
    assert len(alerts) == 1
    assert alerts[0]["severity"] == 3
    assert "stance changed" in alerts[0]["description"]

    # other tickers see no alerts
    autopilot._dossier_cache.clear()
    r2 = await client.get("/api/v1/autopilot/desk/A6XX/header")
    assert r2.json()["data"]["payload"]["alerts"] == []
