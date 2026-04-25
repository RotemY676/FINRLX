"""Phase 7C.1 tests: benchmark truthfulness — all three agents must execute."""
import pytest


@pytest.mark.asyncio
async def test_all_three_agents_execute(client):
    """Default benchmark executes all three required agents."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "completed"
    assert data["is_complete_comparison"] is True
    executed = data["executed_agents"]
    assert "heuristic_baseline" in executed
    assert "random_valid" in executed
    assert "score_weighted_baseline" in executed


@pytest.mark.asyncio
async def test_score_weighted_in_metrics(client):
    """score_weighted_baseline appears in metrics_by_agent."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    data = r.json()["data"]
    assert "score_weighted_baseline" in data["metrics_by_agent"]
    m = data["metrics_by_agent"]["score_weighted_baseline"]
    assert "total_return" in m
    assert "total_reward" in m


@pytest.mark.asyncio
async def test_skipped_agents_empty_for_default(client):
    """Default benchmark has no skipped agents."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    data = r.json()["data"]
    assert data["skipped_agents"] == [] or data["skipped_agents"] is None or len(data["skipped_agents"]) == 0


@pytest.mark.asyncio
async def test_unknown_agent_produces_partial(client):
    """Requesting an unknown agent produces partial status."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
        "agent_keys": ["heuristic_baseline", "nonexistent_agent"],
    })
    data = r.json()["data"]
    assert data["status"] == "partial"
    assert data["is_complete_comparison"] is False
    assert any(s["agent_key"] == "nonexistent_agent" for s in data["skipped_agents"])


@pytest.mark.asyncio
async def test_safety_flags_unchanged(client):
    """Safety flags remain correct after fix."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    sf = r.json()["data"]["safety_flags"]
    assert sf["offline_only"] is True
    assert sf["shadow_only"] is True
    assert sf["live_pipeline_influence"] is False
    assert sf["no_broker_execution"] is True
    assert sf["no_publication_influence"] is True
    assert sf["no_recommendation_pollution"] is True


@pytest.mark.asyncio
async def test_recommendations_unaffected(client):
    """/recommendations/current is not affected by benchmarks."""
    await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    r = await client.get("/api/v1/recommendations/current")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_overview_unaffected(client):
    """/overview is not affected by benchmarks."""
    r = await client.get("/api/v1/overview")
    assert r.status_code == 200
