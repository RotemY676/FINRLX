"""Design Sprint 4 tests: scenario simulation, action bar, incident drawer support."""
import pytest

from app.core.database import get_db
from app.main import app


async def _restore_rec_status(status: str = "published"):
    """Restore recommendation status after action tests modify it."""
    from sqlalchemy import update
    from app.models.recommendation import Recommendation
    # Get test DB session
    dep = app.dependency_overrides.get(get_db)
    if dep:
        async for db in dep():
            await db.execute(update(Recommendation).values(status=status))
            await db.commit()
            break


# ── Scenario simulation ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_scenario_baseline(client):
    """GET /scenario/baseline returns default parameters."""
    r = await client.get("/api/v1/scenario/baseline")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["horizon_days"] == 42
    assert data["rate_shock_bps"] == 0
    assert data["momentum_engine_on"] is True
    assert data["flow_engine_on"] is False


@pytest.mark.asyncio
async def test_scenario_simulate_baseline(client):
    """POST /scenario/simulate with baseline params returns is_modified=false."""
    r = await client.post("/api/v1/scenario/simulate", json={
        "horizon_days": 42, "rate_shock_bps": 0, "correlation": 0.55,
        "earnings_revision_weight": 0.60, "momentum_engine_on": True,
        "flow_engine_on": False, "policy_constraints_on": True,
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["is_modified"] is False
    assert len(data["deltas"]) == 0


@pytest.mark.asyncio
async def test_scenario_simulate_modified(client):
    """POST /scenario/simulate with modified params returns deltas."""
    r = await client.post("/api/v1/scenario/simulate", json={
        "horizon_days": 90, "rate_shock_bps": 100, "correlation": 0.80,
        "earnings_revision_weight": 0.40, "momentum_engine_on": True,
        "flow_engine_on": True, "policy_constraints_on": False,
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["is_modified"] is True
    assert len(data["deltas"]) == 3
    assert any(d["metric"] == "Weight" for d in data["deltas"])
    assert any(d["metric"] == "Confidence" for d in data["deltas"])
    assert any(d["metric"] == "Expected Δ" for d in data["deltas"])


@pytest.mark.asyncio
async def test_scenario_simulate_warnings(client):
    """POST /scenario/simulate with extreme params returns warnings."""
    r = await client.post("/api/v1/scenario/simulate", json={
        "horizon_days": 42, "rate_shock_bps": 150, "correlation": 0.55,
        "earnings_revision_weight": 0.60, "momentum_engine_on": False,
        "flow_engine_on": False, "policy_constraints_on": False,
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data["warnings"]) >= 2  # rate shock + momentum disabled + policy disabled


@pytest.mark.asyncio
async def test_scenario_simulate_validation(client):
    """POST /scenario/simulate rejects invalid params."""
    r = await client.post("/api/v1/scenario/simulate", json={
        "horizon_days": 3,  # below minimum of 7
        "rate_shock_bps": 0, "correlation": 0.55,
        "earnings_revision_weight": 0.60, "momentum_engine_on": True,
        "flow_engine_on": False, "policy_constraints_on": True,
    })
    assert r.status_code == 422  # validation error


# ── Action bar ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_action_save_thesis(client):
    """POST /actions/save-thesis updates recommendation status."""
    r = await client.post("/api/v1/actions/save-thesis")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["success"] is True
    assert data["new_status"] == "staged"
    assert data["action"] == "save_thesis"
    await _restore_rec_status()


@pytest.mark.asyncio
async def test_action_promote_paper(client):
    """POST /actions/promote-paper updates recommendation status."""
    r = await client.post("/api/v1/actions/promote-paper")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["success"] is True
    assert data["new_status"] == "paper"
    await _restore_rec_status()


@pytest.mark.asyncio
async def test_action_defer(client):
    """POST /actions/defer with reason defers the decision."""
    r = await client.post("/api/v1/actions/defer", json={"reason": "Awaiting earnings print"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["success"] is True
    assert data["new_status"] == "deferred"
    assert "Awaiting earnings print" in data["message"]
    await _restore_rec_status()


@pytest.mark.asyncio
async def test_action_defer_no_body(client):
    """POST /actions/defer without body still works."""
    r = await client.post("/api/v1/actions/defer")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["success"] is True
    await _restore_rec_status()
