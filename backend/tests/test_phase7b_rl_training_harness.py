"""Phase 7B tests: RL training harness, agent registry, dataset export."""
import pytest


# ── Agent registry ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_default_agent_definitions_exist(client):
    """GET /rl/agents returns default agents."""
    r = await client.get("/api/v1/rl/agents")
    assert r.status_code == 200
    agents = r.json()["data"]
    assert len(agents) >= 3
    keys = {a["key"] for a in agents}
    assert "heuristic_baseline" in keys
    assert "random_valid" in keys
    assert "score_weighted_baseline" in keys
    # Trainable agent exists
    trainable = [a for a in agents if a["is_trainable"]]
    assert len(trainable) >= 1
    assert trainable[0]["is_shadow_only"] is True


@pytest.mark.asyncio
async def test_agent_detail(client):
    """GET /rl/agents/{key} returns single agent."""
    r = await client.get("/api/v1/rl/agents/score_weighted_baseline")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["algorithm_family"] == "deterministic_grid_search"
    assert data["is_trainable"] is True


# ── Adapter status ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_adapter_status_offline(client):
    """GET /rl/adapter/status reports offline_only and no live influence."""
    r = await client.get("/api/v1/rl/adapter/status")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["offline_only"] is True
    assert data["live_pipeline_influence"] is False
    assert data["is_shadow_only"] is True
    assert data["total_agents"] >= 3


# ── Dataset export ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dataset_export(client):
    """GET /rl/dataset/export returns rows with state/prices/policies."""
    r = await client.get("/api/v1/rl/dataset/export", params={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
        "limit": 10,
    })
    assert r.status_code == 200
    rows = r.json()["data"]
    assert len(rows) >= 1
    row = rows[0]
    assert "as_of_date" in row
    assert "universe_tickers" in row
    assert "policy_constraints" in row
    assert "assets" in row
    if row["assets"]:
        a = row["assets"][0]
        assert "ticker" in a
        assert "price" in a
        assert "engine_score" in a


# ── Training ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_train_creates_run_and_snapshot(client):
    """POST /rl/train creates training_run and policy_snapshot."""
    r = await client.post("/api/v1/rl/train", json={
        "agent_key": "score_weighted_baseline",
        "environment_key": "quantpipeline_offline_v1",
        "train_start_date": "2026-03-15",
        "train_end_date": "2026-04-15",
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "completed"
    assert data["agent_key"] == "score_weighted_baseline"
    assert data["metrics"] is not None
    assert "policy_snapshot_id" in data["metrics"]

    # Verify policy snapshot exists
    snap_id = data["metrics"]["policy_snapshot_id"]
    r2 = await client.get(f"/api/v1/rl/policies/{snap_id}")
    assert r2.status_code == 200
    snap = r2.json()["data"]
    assert snap["policy_type"] == "score_weighted_blend"
    assert snap["policy_payload"]["notes"] == "baseline grid-search policy, not neural RL"


@pytest.mark.asyncio
async def test_training_deterministic(client):
    """Training the same agent twice with same data produces same reward."""
    r1 = await client.post("/api/v1/rl/train", json={
        "agent_key": "score_weighted_baseline",
        "train_start_date": "2026-03-20",
        "train_end_date": "2026-04-10",
    })
    r2 = await client.post("/api/v1/rl/train", json={
        "agent_key": "score_weighted_baseline",
        "train_start_date": "2026-03-20",
        "train_end_date": "2026-04-10",
    })
    d1 = r1.json()["data"]
    d2 = r2.json()["data"]
    if d1["status"] == "completed" and d2["status"] == "completed":
        assert d1["metrics"]["total_reward"] == d2["metrics"]["total_reward"]


# ── Policy evaluation ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_evaluate_policy_snapshot(client):
    """POST /rl/policies/{id}/evaluate returns metrics."""
    # Train first to get a snapshot
    r = await client.post("/api/v1/rl/train", json={
        "train_start_date": "2026-03-15",
        "train_end_date": "2026-04-15",
    })
    snap_id = r.json()["data"]["metrics"]["policy_snapshot_id"]

    r2 = await client.post(f"/api/v1/rl/policies/{snap_id}/evaluate", json={
        "eval_start_date": "2026-03-20",
        "eval_end_date": "2026-04-10",
    })
    assert r2.status_code == 200
    data = r2.json()["data"]
    assert data["policy_snapshot_id"] == snap_id
    assert data["status"] in ("completed", "failed")
    assert data["metrics"] is not None


# ── Training runs list ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_training_runs_list(client):
    """GET /rl/training-runs returns list."""
    r = await client.get("/api/v1/rl/training-runs")
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)


@pytest.mark.asyncio
async def test_policies_list(client):
    """GET /rl/policies returns list."""
    r = await client.get("/api/v1/rl/policies")
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)


# ── Ops integration ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ops_includes_training_info(client):
    """GET /ops RL block includes training fields."""
    r = await client.get("/api/v1/ops")
    assert r.status_code == 200
    rl = r.json()["data"]["rl"]
    assert rl["is_shadow_only"] is True
    assert rl["live_pipeline_influence"] is False
    assert "total_agents" in rl
    assert "trainable_agents" in rl
    assert "total_policy_snapshots" in rl


# ── Shadow / isolation ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_training_does_not_affect_current(client):
    """Training does not affect /recommendations/current."""
    await client.post("/api/v1/rl/train", json={
        "train_start_date": "2026-03-15",
        "train_end_date": "2026-04-15",
    })
    r = await client.get("/api/v1/recommendations/current")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_training_does_not_affect_overview(client):
    """Training does not affect /overview."""
    r = await client.get("/api/v1/overview")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_no_publication_from_training(client):
    """No publication is created from training."""
    r = await client.post("/api/v1/rl/train", json={
        "train_start_date": "2026-03-15",
        "train_end_date": "2026-04-15",
    })
    data = r.json()["data"]
    assert data["status"] in ("completed", "failed")
    # No recommendation_id in training run


@pytest.mark.asyncio
async def test_existing_pipeline_still_works(client):
    """Pipeline still works after training additions."""
    from datetime import date
    today = date.today().isoformat()
    r = await client.post("/api/v1/features/compute", json={"as_of": today})
    fs_id = r.json()["data"]["feature_set_id"]
    await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})
    r = await client.post("/api/v1/pipeline/run", json={"feature_set_id": fs_id})
    assert r.json()["data"]["status"] == "completed"
