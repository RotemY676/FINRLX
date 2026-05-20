"""Phase MVP-7 — /healthz deep probe tests.

The probe is hit by load-balancers and uptime monitors. The contract is:

- 200 + status="ok" or "degraded" when every hard check passes.
- 503 + status="unhealthy" when any hard check (database) fails.
- Always returns a JSON body that lists every individual check result so
  operators can curl and diagnose without opening a log.
"""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_healthz_returns_ok_with_seed_data(client):
    r = await client.get("/healthz")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] in ("ok", "degraded"), body
    assert "version" in body
    assert isinstance(body["checks"], list)
    assert len(body["checks"]) >= 3


@pytest.mark.asyncio
async def test_healthz_reports_database_check_passing(client):
    body = (await client.get("/healthz")).json()
    db = next(c for c in body["checks"] if c["name"] == "database")
    assert db["ok"] is True
    assert db["severity"] == "hard"
    assert db["detail"] == "connected"


@pytest.mark.asyncio
async def test_healthz_includes_market_data_freshness(client):
    body = (await client.get("/healthz")).json()
    md = next(c for c in body["checks"] if c["name"] == "market_data_freshness")
    # conftest seeds 30 days of bars; freshness check should report a recent date.
    assert md["severity"] == "soft"
    assert "newest_bar_" in md["detail"] or "stale" in md["detail"]


@pytest.mark.asyncio
async def test_healthz_includes_recent_recommendation(client):
    body = (await client.get("/healthz")).json()
    rec = next(c for c in body["checks"] if c["name"] == "recent_recommendation")
    # conftest seeds one recommendation; the info-level check should be OK.
    assert rec["severity"] == "info"
    assert rec["ok"] is True


@pytest.mark.asyncio
async def test_healthz_status_envelope_keys(client):
    body = (await client.get("/healthz")).json()
    assert set(body.keys()) >= {"status", "version", "checks"}
    for c in body["checks"]:
        assert set(c.keys()) == {"name", "ok", "severity", "detail"}
