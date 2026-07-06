"""Program LEAP S2/S6 — dossier persistence + comparison tests
(gates: D34 persistence, GS6.1 mixed warm/cold, S6 limits, D39 budget)."""
from __future__ import annotations

import time
from datetime import date, timedelta
from unittest import mock

import pytest

from app.services import autopilot
from app.services import autopilot_store as store
from app.services.single_ticker_analysis import Bars

# ── fixtures: synthetic market via the same seams the autopilot suite uses ──


def make_bars(n: int = 420, seed_shift: float = 0.0) -> Bars:
    dates, closes, vols = [], [], []
    d = date(2024, 6, 3)
    px = 100.0 + seed_shift
    i = 0
    while len(dates) < n:
        if d.weekday() < 5:
            px *= 1.0 + (0.004 if (i // 20) % 2 == 0 else -0.002) + 0.0004 * ((i * 7) % 5 - 2)
            dates.append(d)
            closes.append(round(px, 4))
            vols.append(1_000_000 + (i % 7) * 10_000)
            i += 1
        d += timedelta(days=1)
    return Bars(dates=dates, closes=closes, volumes=vols,
                highs=[c * 1.01 for c in closes], lows=[c * 0.99 for c in closes])


SUITE_TICKERS = ("PERS1", "PERS2", "PERS3", "CMPA", "CMPB", "ONLY", "NODATA",
                 "EPA", "EPB", "EPP", "BUDG")


@pytest.fixture(autouse=True)
def _cleanup_rows():
    """Leave no dossier rows behind for other suites (S8 scans the table)."""
    yield
    import asyncio
    from sqlalchemy import delete
    from app.models.autopilot import AutopilotDossier
    from tests.conftest import test_session_factory

    async def _wipe():
        async with test_session_factory() as db:
            await db.execute(
                delete(AutopilotDossier).where(AutopilotDossier.ticker.in_(SUITE_TICKERS))
            )
            await db.commit()
    asyncio.get_event_loop().run_until_complete(_wipe())


def _patch_market(monkeypatch, bars_by_ticker: dict[str, Bars]):
    def fake_history(sym, days):
        return bars_by_ticker.get(sym, Bars(dates=[], closes=[], volumes=[], highs=[], lows=[]))
    monkeypatch.setattr(autopilot, "fetch_history", fake_history)
    monkeypatch.setattr(autopilot, "fetch_news", lambda sym, limit=20: ([], False))
    autopilot._dossier_cache.clear()


# ── persistence (D34) ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_persist_then_load_roundtrip_and_upsert(monkeypatch):
    from tests.conftest import test_session_factory

    _patch_market(monkeypatch, {"PERS1": make_bars()})
    dossier = autopilot.build_dossier("PERS1")
    async with test_session_factory() as db:
        await store.persist_dossier(db, dossier)
        await store.persist_dossier(db, dossier)  # upsert, not duplicate
        await db.commit()
        loaded = await store.load_persisted(db, "PERS1")
        from sqlalchemy import func, select
        from app.models.autopilot import AutopilotDossier
        count = (await db.execute(
            select(func.count()).select_from(AutopilotDossier)
            .where(AutopilotDossier.ticker == "PERS1")
        )).scalar_one()
    assert count == 1
    assert loaded is not None
    assert loaded["ticker"] == "PERS1"
    assert loaded["served_from_persistence"] is True
    assert loaded["config_version"] == autopilot.CONFIG_VERSION


@pytest.mark.asyncio
async def test_get_or_build_serves_persisted_when_config_matches(monkeypatch):
    from tests.conftest import test_session_factory

    _patch_market(monkeypatch, {"PERS2": make_bars()})
    dossier = autopilot.build_dossier("PERS2")
    calls = {"n": 0}

    def counting_build(ticker, **kw):
        calls["n"] += 1
        return dossier
    monkeypatch.setattr(store, "build_dossier", counting_build)

    async with test_session_factory() as db:
        await store.persist_dossier(db, dossier)
        await db.commit()
        served = await store.get_or_build_dossier(db, "PERS2")
    assert served["served_from_persistence"] is True
    assert calls["n"] == 0  # warm path: no rebuild


@pytest.mark.asyncio
async def test_get_or_build_rebuilds_on_stale_config_version(monkeypatch):
    from tests.conftest import test_session_factory

    _patch_market(monkeypatch, {"PERS3": make_bars()})
    stale = autopilot.build_dossier("PERS3")
    stale = dict(stale, config_version="obsolete-version")
    async with test_session_factory() as db:
        await store.persist_dossier(db, stale)
        await db.commit()
        served = await store.get_or_build_dossier(db, "PERS3")
        await db.commit()
    assert served.get("served_from_persistence") is not True
    assert served["config_version"] == autopilot.CONFIG_VERSION


# ── comparison (S6) ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_comparison_mixed_warm_cold_and_divergence(monkeypatch):
    from tests.conftest import test_session_factory

    _patch_market(monkeypatch, {"CMPA": make_bars(), "CMPB": make_bars(seed_shift=40.0)})
    warm = autopilot.build_dossier("CMPA")
    async with test_session_factory() as db:
        await store.persist_dossier(db, warm)  # CMPA warm, CMPB cold
        await db.commit()
        result = await store.build_comparison(db, ["cmpa", "CMPB", "CMPA"])  # dedupe+normalize
        await db.commit()
    assert result["tickers"] == ["CMPA", "CMPB"]
    assert len(result["columns"]) == 2
    served = {c["ticker"]: c["served_from_cache"] for c in result["columns"]}
    assert served["CMPA"] is True
    for col in result["columns"]:
        assert col["selected_model"] is not None
        assert col["latest_bar_date"]
    assert isinstance(result["divergence_highlights"], list)
    assert any("not investment advice" in d.lower() for d in result["disclaimers"])


@pytest.mark.asyncio
async def test_comparison_rejects_bad_cardinality_and_contains_per_ticker_errors(monkeypatch):
    from tests.conftest import test_session_factory

    _patch_market(monkeypatch, {"ONLY": make_bars()})
    async with test_session_factory() as db:
        with pytest.raises(ValueError):
            await store.build_comparison(db, ["ONLY"])
        with pytest.raises(ValueError):
            await store.build_comparison(db, ["A", "B", "C", "D", "E"])
        result = await store.build_comparison(db, ["ONLY", "NODATA"])
    assert [c["ticker"] for c in result["columns"]] == ["ONLY"]
    assert "NODATA" in result["errors"]


# ── endpoints ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_compare_endpoint_contract(client, monkeypatch):
    _patch_market(monkeypatch, {"EPA": make_bars(), "EPB": make_bars(seed_shift=25.0)})
    r = await client.get("/api/v1/autopilot/compare?tickers=EPA,EPB")
    assert r.status_code == 200, r.text
    body = r.json()["data"]
    assert body["tickers"] == ["EPA", "EPB"]
    assert len(body["columns"]) == 2


@pytest.mark.asyncio
async def test_compare_endpoint_rejects_cardinality(client):
    r = await client.get("/api/v1/autopilot/compare?tickers=ONE")
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_dossier_endpoint_persists_result(client, monkeypatch):
    from tests.conftest import test_session_factory

    _patch_market(monkeypatch, {"EPP": make_bars()})
    r = await client.get("/api/v1/autopilot/dossier?ticker=EPP")
    assert r.status_code == 200
    async with test_session_factory() as db:
        loaded = await store.load_persisted(db, "EPP")
    assert loaded is not None and loaded["ticker"] == "EPP"


# ── D39 runtime budget ──────────────────────────────────────────────────────


def test_dossier_build_within_budget_on_fixture(monkeypatch):
    """Cold build (ex-network, ex-RL) must stay far inside the D39 budget;
    3 seconds here is a conservative CI-safe stand-in for the 6-minute cold
    ceiling (network dominates the rest in production)."""
    _patch_market(monkeypatch, {"BUDG": make_bars(500)})
    t0 = time.time()
    dossier = autopilot.build_dossier("BUDG")
    elapsed = time.time() - t0
    assert dossier["sections"]["model_insight"]["winner"] is not None
    assert elapsed < 3.0, f"cold fixture build took {elapsed:.2f}s"
