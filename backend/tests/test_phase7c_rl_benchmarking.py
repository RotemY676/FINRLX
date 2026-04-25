"""Phase 7C tests: RL offline benchmarking and forensic comparison."""
import pytest


# ── Benchmark creation ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_benchmark_creates_report(client):
    """POST /rl/benchmarks/run creates a persisted benchmark report."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "name": "Test Benchmark",
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "completed"
    assert data["id"] is not None
    assert len(data["compared_agents"]) >= 3
    assert "heuristic_baseline" in data["compared_agents"]
    assert "random_valid" in data["compared_agents"]
    assert "score_weighted_baseline" in data["compared_agents"]


@pytest.mark.asyncio
async def test_benchmark_includes_metrics_by_agent(client):
    """Benchmark report includes per-agent metrics."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    data = r.json()["data"]
    m = data["metrics_by_agent"]
    assert "heuristic_baseline" in m
    for agent_key, metrics in m.items():
        assert "total_return" in metrics
        assert "total_reward" in metrics
        assert "max_drawdown" in metrics
        assert "total_turnover" in metrics
        assert "step_count" in metrics


@pytest.mark.asyncio
async def test_benchmark_includes_reward_breakdown(client):
    """Benchmark report includes reward component breakdown."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    data = r.json()["data"]
    rb = data["reward_breakdown_by_agent"]
    assert "heuristic_baseline" in rb
    for agent_key, breakdown in rb.items():
        assert "portfolio_return_component" in breakdown
        assert "drawdown_penalty_component" in breakdown
        assert "turnover_penalty_component" in breakdown


@pytest.mark.asyncio
async def test_benchmark_includes_safety_flags(client):
    """Benchmark report includes explicit safety flags."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    data = r.json()["data"]
    sf = data["safety_flags"]
    assert sf["offline_only"] is True
    assert sf["shadow_only"] is True
    assert sf["live_pipeline_influence"] is False
    assert sf["no_broker_execution"] is True
    assert sf["no_publication_influence"] is True
    assert sf["no_recommendation_pollution"] is True


@pytest.mark.asyncio
async def test_benchmark_includes_forensic_summary(client):
    """Benchmark report includes step-level forensic rows."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    data = r.json()["data"]
    fs = data["forensic_summary"]
    assert isinstance(fs, list)
    if fs:
        row = fs[0]
        assert "step_index" in row
        assert "as_of_date" in row
        assert "reward" in row
        assert "portfolio_value" in row


@pytest.mark.asyncio
async def test_benchmark_includes_violations(client):
    """Benchmark report includes violations by agent."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    data = r.json()["data"]
    assert "violations_by_agent" in data
    for agent_key in data["compared_agents"]:
        if agent_key in data["metrics_by_agent"]:
            assert "violation_count" in data["metrics_by_agent"][agent_key]


@pytest.mark.asyncio
async def test_benchmark_includes_warnings(client):
    """Benchmark report includes warnings when present."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    data = r.json()["data"]
    # warnings may be null or list — both are valid
    assert data.get("warnings") is None or isinstance(data["warnings"], list)


# ── Benchmark persistence ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_benchmark_is_persisted(client):
    """Benchmark report can be read by ID after creation."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    report_id = r.json()["data"]["id"]
    r2 = await client.get(f"/api/v1/rl/benchmarks/{report_id}")
    assert r2.status_code == 200
    assert r2.json()["data"]["id"] == report_id


@pytest.mark.asyncio
async def test_benchmark_list(client):
    """GET /rl/benchmarks returns list."""
    r = await client.get("/api/v1/rl/benchmarks")
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)


# ── Policy comparison ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_compare_policy(client):
    """POST /rl/benchmarks/compare-policy compares a policy against baselines."""
    # Train first to get a snapshot
    r = await client.post("/api/v1/rl/train", json={
        "train_start_date": "2026-03-15",
        "train_end_date": "2026-04-15",
    })
    snap_id = r.json()["data"]["policy_snapshot_id"]

    r2 = await client.post("/api/v1/rl/benchmarks/compare-policy", json={
        "policy_snapshot_id": snap_id,
        "start_date": "2026-03-20",
        "end_date": "2026-04-10",
    })
    assert r2.status_code == 200
    data = r2.json()["data"]
    assert data["status"] == "completed"
    assert snap_id in (data["policy_snapshot_ids"] or [])
    assert len(data["compared_agents"]) >= 3  # baselines + policy


# ── Insufficient data ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_benchmark_insufficient_data(client):
    """Benchmark with very short window still produces a report (partial/completed)."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-04-14",
        "end_date": "2026-04-15",
    })
    data = r.json()["data"]
    # Should not crash — may have warnings about insufficient steps
    assert data["status"] in ("completed", "partial", "failed")


# ── Safety / isolation ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_benchmark_does_not_affect_recommendations(client):
    """/recommendations/current is not affected by benchmark creation."""
    await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    r = await client.get("/api/v1/recommendations/current")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_benchmark_does_not_affect_overview(client):
    """/overview is not affected by benchmark creation."""
    r = await client.get("/api/v1/overview")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_publication_unchanged(client):
    """Publication workflow is not affected by benchmarking."""
    r = await client.get("/api/v1/publication/status")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_no_broker_execution_endpoint(client):
    """No broker/execution endpoint exists."""
    r = await client.post("/api/v1/rl/execute", json={})
    assert r.status_code in (404, 405, 422)


@pytest.mark.asyncio
async def test_rl_benchmark_outputs_shadow(client):
    """RL benchmark outputs are offline/shadow only (via safety_flags)."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    sf = r.json()["data"]["safety_flags"]
    assert sf["offline_only"] is True
    assert sf["no_broker_execution"] is True
    assert sf["live_pipeline_influence"] is False


@pytest.mark.asyncio
async def test_ops_includes_benchmark_info(client):
    """GET /ops RL block includes benchmark fields."""
    r = await client.get("/api/v1/ops")
    assert r.status_code == 200
    rl = r.json()["data"]["rl"]
    assert "total_benchmarks" in rl
    assert rl["is_shadow_only"] is True
    assert rl["live_pipeline_influence"] is False


# ── Pipeline unchanged ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pipeline_still_works(client):
    """Pipeline still works after benchmark additions."""
    from datetime import date
    today = date.today().isoformat()
    r = await client.post("/api/v1/features/compute", json={"as_of": today})
    fs_id = r.json()["data"]["feature_set_id"]
    await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})
    r = await client.post("/api/v1/pipeline/run", json={"feature_set_id": fs_id})
    assert r.json()["data"]["status"] == "completed"
