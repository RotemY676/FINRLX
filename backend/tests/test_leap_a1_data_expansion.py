"""Program LEAP A1 — data-expansion tests.

Gates: adapter contracts incl. absence paths; keyless path always green;
XBRL parsing on fixtures (no network in tests); the three new dossier
sections present with honest states; and the stance-uninfluenced regression
(fundamentals/filings/insider must never move the composite stance)."""
from __future__ import annotations

from unittest import mock

from app.services.data_providers import finnhub_extras, sec_xbrl

# ── SEC XBRL parsing (fixture-driven, zero network) ─────────────────────────

FACTS_FIXTURE = {
    "entityName": "TESTCO INC",
    "facts": {
        "us-gaap": {
            "Revenues": {"units": {"USD": [
                {"form": "10-K", "fp": "FY", "fy": 2022, "end": "2022-12-31", "val": 100.0, "filed": "2023-02-01"},
                {"form": "10-K", "fp": "FY", "fy": 2023, "end": "2023-12-31", "val": 120.0, "filed": "2024-02-01"},
                {"form": "10-K", "fp": "FY", "fy": 2024, "end": "2024-12-31", "val": 150.0, "filed": "2025-02-01"},
                # restated 2023 value filed later must win
                {"form": "10-K", "fp": "FY", "fy": 2023, "end": "2023-12-31", "val": 125.0, "filed": "2024-06-01"},
                # quarterly rows must be ignored
                {"form": "10-Q", "fp": "Q2", "fy": 2024, "end": "2024-06-30", "val": 70.0, "filed": "2024-08-01"},
            ]}},
            "NetIncomeLoss": {"units": {"USD": [
                {"form": "10-K", "fp": "FY", "fy": 2023, "end": "2023-12-31", "val": 25.0, "filed": "2024-02-01"},
                {"form": "10-K", "fp": "FY", "fy": 2024, "end": "2024-12-31", "val": 30.0, "filed": "2025-02-01"},
            ]}},
            "Liabilities": {"units": {"USD": [
                {"form": "10-K", "fp": "FY", "fy": 2024, "end": "2024-12-31", "val": 200.0, "filed": "2025-02-01"},
            ]}},
            "StockholdersEquity": {"units": {"USD": [
                {"form": "10-K", "fp": "FY", "fy": 2024, "end": "2024-12-31", "val": 100.0, "filed": "2025-02-01"},
            ]}},
        },
        "dei": {
            "EntityCommonStockSharesOutstanding": {"units": {"shares": [
                {"form": "10-K", "fp": "FY", "fy": 2023, "end": "2023-12-31", "val": 1000, "filed": "2024-02-01"},
                {"form": "10-K", "fp": "FY", "fy": 2024, "end": "2024-12-31", "val": 1100, "filed": "2025-02-01"},
            ]}},
        },
    },
}


def test_xbrl_trends_parse_fixture(monkeypatch):
    monkeypatch.setattr(sec_xbrl, "resolve_cik", lambda t: 12345)
    monkeypatch.setattr(sec_xbrl, "_fetch_facts", lambda cik: FACTS_FIXTURE)
    out = sec_xbrl.build_xbrl_trends("TEST")
    assert out["available"] is True and out["entity"] == "TESTCO INC"
    rev = {r["fy"]: r["value"] for r in out["revenue"]}
    assert rev == {2022: 100.0, 2023: 125.0, 2024: 150.0}  # restatement wins; 10-Q ignored
    margins = {r["fy"]: r["value"] for r in out["net_margin"]}
    assert margins[2024] == 0.2  # 30/150
    assert out["leverage_liab_over_equity"][-1]["value"] == 2.0
    assert out["dilution_yoy"][-1]["value"] == 0.1  # 1100/1000 - 1


def test_xbrl_no_cik_degrades():
    with mock.patch.object(sec_xbrl, "resolve_cik", return_value=None):
        out = sec_xbrl.build_xbrl_trends("ZZZZ")
    assert out == {"available": False, "reason": "no_sec_cik", "source": "sec_xbrl"}


def test_xbrl_unreachable_degrades(monkeypatch):
    monkeypatch.setattr(sec_xbrl, "resolve_cik", lambda t: 1)
    monkeypatch.setattr(sec_xbrl, "_fetch_facts", lambda cik: None)
    assert sec_xbrl.build_xbrl_trends("T")["reason"] == "sec_unreachable"


# ── Finnhub extras (absence + fixture paths) ────────────────────────────────


def test_extras_keyless_absence(monkeypatch):
    monkeypatch.setattr(finnhub_extras, "_key", lambda: None)
    for fn in (finnhub_extras.insider_sentiment, finnhub_extras.filings_tone,
               finnhub_extras.similarity_index):
        out = fn("NVDA")
        assert out["available"] is False and out["reason"] == "no_api_key"


def test_insider_sentiment_fixture(monkeypatch):
    payload = {"data": [
        {"year": 2026, "month": m, "mspr": float(m), "change": m * 10} for m in range(1, 15)
    ]}
    monkeypatch.setattr(finnhub_extras, "_get", lambda p, q: (payload, None))
    out = finnhub_extras.insider_sentiment("NVDA")
    assert out["available"] is True
    assert len(out["series_12m"]) == 12
    assert out["latest_mspr"] == 14.0
    assert "noisy" in out["caveat"]


def test_similarity_index_fixture(monkeypatch):
    payload = {"similarity": [
        {"form": "10-K", "filedDate": "2025-02-01", "cosineAll": 0.93},
        {"form": "10-K", "filedDate": "2026-02-01", "cosineAll": 0.71},
    ]}
    monkeypatch.setattr(finnhub_extras, "_get", lambda p, q: (payload, None))
    out = finnhub_extras.similarity_index("NVDA")
    assert out["available"] is True and out["cosine_all"] == 0.71
    assert "not a directional call" in out["read"]


def test_tier_or_auth_reported(monkeypatch):
    monkeypatch.setattr(finnhub_extras, "_get", lambda p, q: (None, "tier_or_auth"))
    assert finnhub_extras.insider_sentiment("NVDA")["reason"] == "tier_or_auth"


# ── dossier wiring + stance regression ──────────────────────────────────────


def _bars():
    from datetime import date, timedelta

    from app.services.single_ticker_analysis import Bars

    dates, closes = [], []
    d, px, i = date(2024, 6, 3), 100.0, 0
    while len(dates) < 420:
        if d.weekday() < 5:
            px *= 1.0 + (0.004 if (i // 20) % 2 == 0 else -0.002)
            dates.append(d)
            closes.append(round(px, 4))
            i += 1
        d += timedelta(days=1)
    return Bars(dates=dates, closes=closes, volumes=[1_000_000] * 420,
                highs=[c * 1.01 for c in closes], lows=[c * 0.99 for c in closes])


def test_dossier_gains_sections_with_honest_states_and_stance_unchanged(monkeypatch):
    from app.services import autopilot

    monkeypatch.setattr(autopilot, "fetch_history", lambda s, days: _bars())
    monkeypatch.setattr(autopilot, "fetch_news", lambda s, limit=20: ([], False))
    autopilot._dossier_cache.clear()

    # A) all A1 sources absent -> honest degraded sections
    import app.services.data_providers.sec_xbrl as x
    import app.services.data_providers.finnhub_extras as fx

    monkeypatch.setattr(x, "resolve_cik", lambda t: None)
    monkeypatch.setattr(fx, "_key", lambda: None)
    d_absent = autopilot.build_dossier("A1T")
    secs = d_absent["sections"]
    assert secs["fundamentals"]["available"] is False
    assert secs["filings"]["available"] is False
    assert secs["insider"]["available"] is False
    assert any(s["stage"] == "fundamentals" for s in d_absent["stages"])

    # B) sources present -> sections real, and the STANCE IS BYTE-IDENTICAL
    autopilot._dossier_cache.clear()
    monkeypatch.setattr(x, "resolve_cik", lambda t: 12345)
    monkeypatch.setattr(x, "_fetch_facts", lambda cik: FACTS_FIXTURE)
    monkeypatch.setattr(
        fx, "_get",
        lambda p, q: ({"data": [{"year": 2026, "month": 6, "mspr": 42.0, "change": 5}]}
                      if "insider" in p else
                      {"similarity": [{"form": "10-K", "filedDate": "2026-02-01", "cosineAll": 0.8}]}
                      if "similarity" in p else
                      ([{"form": "10-K", "filedDate": "2026-02-01", "accessNumber": "acc-1"}]
                       if p == "/stock/filings" else
                       {"sentiment": {"negative": 0.1, "positive": 0.2, "uncertainty": 0.1,
                                      "litigious": 0.0, "polarity": 0.5}}),
                      None),
    )
    d_present = autopilot.build_dossier("A1T2")
    secs2 = d_present["sections"]
    assert secs2["fundamentals"]["xbrl"]["available"] is True
    assert secs2["insider"]["latest_mspr"] == 42.0
    assert secs2["filings"]["tone"]["available"] is True
    # regression: identical bars => identical stance/composite regardless of A1 data
    assert d_present["summary"]["stance"] == d_absent["summary"]["stance"]
    assert d_present["summary"]["composite_score"] == d_absent["summary"]["composite_score"]
