"""Program LEAP S8 — dossier auto-refresh + material-change tests
(gates GS8.1 deterministic refresh set, GS8.2 change-rule matrix,
GS8.3 evidence-linked notifications)."""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import delete, select

from app.models.autopilot import AutopilotDossier
from app.models.ops import Incident
from app.services import autopilot_refresh as ar
from app.services.autopilot import CONFIG_VERSION

NOW = datetime(2026, 6, 10, 14, 0, tzinfo=UTC)  # Wednesday
EXPECTED = "2026-06-10"


def _payload(ticker: str, regime="uptrend", stance="constructive", winner="momo") -> dict:
    return {
        "ticker": ticker,
        "config_version": CONFIG_VERSION,
        "freshness": {"latest_bar": EXPECTED},
        "summary": {"regime": regime, "stance": stance},
        "sections": {"model_insight": {"winner": {"key": winner, "name": winner}}},
    }


def _row(ticker: str, latest_bar: str, age_days: int = 1,
         config: str = CONFIG_VERSION, payload: dict | None = None) -> AutopilotDossier:
    return AutopilotDossier(
        ticker=ticker,
        latest_bar_date=latest_bar,
        config_version=config,
        generated_at=NOW - timedelta(days=age_days),
        payload_json=json.dumps(payload or _payload(ticker)),
    )


async def _reset(db, tickers):
    await db.execute(delete(AutopilotDossier).where(AutopilotDossier.ticker.in_(tickers)))
    await db.execute(delete(Incident).where(Incident.title.like(f"{ar.INCIDENT_TITLE_PREFIX}%")))
    await db.commit()


# ── change-rule matrix (GS8.2) ──────────────────────────────────────────────


def test_material_change_matrix():
    base = _payload("X")
    assert ar.material_changes(base, _payload("X")) == []
    rules = {c["rule"] for c in ar.material_changes(base, _payload("X", regime="risk-off"))}
    assert rules == {"regime_flip"}
    rules = {c["rule"] for c in ar.material_changes(base, _payload("X", stance="cautious"))}
    assert rules == {"stance_change"}
    rules = {c["rule"] for c in ar.material_changes(base, _payload("X", winner="ml_ridge"))}
    assert rules == {"tournament_winner_change"}
    all3 = ar.material_changes(
        base, _payload("X", regime="risk-off", stance="cautious", winner="ml_ridge"))
    assert {c["rule"] for c in all3} == {
        "regime_flip", "stance_change", "tournament_winner_change"}
    assert all("before" in c and "after" in c for c in all3)


# ── refresh set determinism + budget (GS8.1) ────────────────────────────────


@pytest.mark.asyncio
async def test_refresh_set_deterministic_and_budget_aware(monkeypatch):
    from tests.conftest import test_session_factory

    tickers = ["RF1", "RF2", "RF3", "RF4"]
    fresh_calls: list[str] = []

    async def fake_build(db, ticker):
        fresh_calls.append(ticker)
        return _payload(ticker)
    monkeypatch.setattr(ar, "get_or_build_dossier", fake_build)

    async with test_session_factory() as db:
        await _reset(db, tickers)
        db.add(_row("RF1", "2026-06-01", age_days=9))   # stale, oldest
        db.add(_row("RF2", "2026-06-05", age_days=5))   # stale
        db.add(_row("RF3", EXPECTED, age_days=1))       # fresh -> skipped
        db.add(_row("RF4", "2026-06-05", age_days=2))   # stale, newest
        await db.commit()
        report = await ar.refresh_dossiers(db, budget=2, now=NOW)
        await _reset(db, tickers)

    assert report.evaluated == 4
    assert report.refreshed == ["RF1", "RF2"]      # oldest-first, exactly budget
    assert report.skipped_budget == ["RF4"]
    assert report.skipped_fresh == ["RF3"]
    assert fresh_calls == ["RF1", "RF2"]


@pytest.mark.asyncio
async def test_stale_config_version_forces_refresh(monkeypatch):
    from tests.conftest import test_session_factory

    async def fake_build(db, ticker):
        return _payload(ticker)
    monkeypatch.setattr(ar, "get_or_build_dossier", fake_build)

    async with test_session_factory() as db:
        await _reset(db, ["RFCFG"])
        db.add(_row("RFCFG", EXPECTED, config="ancient"))
        await db.commit()
        report = await ar.refresh_dossiers(db, now=NOW)
        await _reset(db, ["RFCFG"])
    assert report.refreshed == ["RFCFG"]


# ── evidence-linked incidents (GS8.3) ───────────────────────────────────────


@pytest.mark.asyncio
async def test_material_change_opens_evidence_linked_incident_idempotently(monkeypatch):
    from tests.conftest import test_session_factory

    async def flip_build(db, ticker):
        return _payload(ticker, regime="risk-off", winner="ml_ridge")
    monkeypatch.setattr(ar, "get_or_build_dossier", flip_build)

    async with test_session_factory() as db:
        await _reset(db, ["RFCHG"])
        db.add(_row("RFCHG", "2026-06-05"))
        await db.commit()
        r1 = await ar.refresh_dossiers(db, now=NOW)
        # simulate the next run: row is stale again, incident still open
        row = (await db.execute(select(AutopilotDossier).where(
            AutopilotDossier.ticker == "RFCHG"))).scalar_one()
        row.latest_bar_date = "2026-06-05"
        await db.flush()
        r2 = await ar.refresh_dossiers(db, now=NOW)
        incidents = (await db.execute(select(Incident).where(
            Incident.title == f"{ar.INCIDENT_TITLE_PREFIX}RFCHG"))).scalars().all()
        await _reset(db, ["RFCHG"])

    assert r1.material_change_incidents == 1
    assert r2.material_change_incidents == 0  # idempotent while open
    assert len(incidents) == 1
    desc = incidents[0].description or ""
    assert "/api/v1/autopilot/dossier?ticker=RFCHG" in desc  # GS8.3 evidence link
    assert "regime_flip" in desc and "not advice" in desc
    assert incidents[0].source == "autopilot_refresh"


@pytest.mark.asyncio
async def test_failed_rebuild_is_contained(monkeypatch):
    from tests.conftest import test_session_factory

    async def boom(db, ticker):
        raise RuntimeError("no data upstream")
    monkeypatch.setattr(ar, "get_or_build_dossier", boom)

    async with test_session_factory() as db:
        await _reset(db, ["RFERR"])
        db.add(_row("RFERR", "2026-06-01"))
        await db.commit()
        report = await ar.refresh_dossiers(db, now=NOW)
        await _reset(db, ["RFERR"])
    assert "RFERR" in report.failed
    assert report.refreshed == []
