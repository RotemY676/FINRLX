"""Design Sprint 2 tests: engine comparison, evidence, regime, activity endpoints."""
import pytest


@pytest.mark.asyncio
async def test_engine_comparison(client):
    r = await client.get("/api/v1/engines/comparison")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_engine_disagreement(client):
    r = await client.get("/api/v1/engines/disagreement")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_evidence(client):
    r = await client.get("/api/v1/engines/evidence")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data is not None
    assert len(data["items"]) >= 1  # real engine-derived or legacy fallback


@pytest.mark.asyncio
async def test_regime(client):
    r = await client.get("/api/v1/regime")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["regime_label"] == "Risk-on · late-cycle"
    assert len(data["signal_posture"]) == 4
    assert len(data["sector_tilts"]) == 5


@pytest.mark.asyncio
async def test_activity(client):
    r = await client.get("/api/v1/activity")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "events" in data
    assert "total" in data
