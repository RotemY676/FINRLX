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
    # data may be None if no engine run has happened yet (no legacy fallback)
    data = r.json()["data"]
    if data is not None:
        assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_regime(client):
    """`/regime` is computed from real bars as of 2026-07-23.

    This test previously asserted `regime_label == "Risk-on · late-cycle"` and
    exact counts of 4 factor postures and 5 sector tilts — all of which were
    hardcoded fabrications in the endpoint. The test was pinning the fiction in
    place, so it would have failed on any honest implementation. It now asserts
    the real contract: a rule-derived label, and empty lists for the things the
    system has no model to produce.
    """
    r = await client.get("/api/v1/regime")
    if r.status_code == 503:
        pytest.skip("benchmark history unavailable in this environment")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["regime_label"] in {"uptrend", "downtrend", "neutral", "risk-off"}
    assert data["benchmark"] == "SPY"
    # No factor-exposure or sector-attribution model exists; these must stay
    # empty and be named in `unavailable` rather than filled with numbers.
    assert data["signal_posture"] == []
    assert data["sector_tilts"] == []
    assert data["unavailable"]


@pytest.mark.asyncio
async def test_activity(client):
    r = await client.get("/api/v1/activity")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "events" in data
    assert "total" in data
