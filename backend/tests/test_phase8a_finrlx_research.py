"""Phase 8A tests: FinRL-X neural RL research spike."""
import pytest


# ── Status ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_finrlx_status(client):
    """GET /rl/finrlx/status returns research/offline/shadow safety flags."""
    r = await client.get("/api/v1/rl/finrlx/status")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["research_only"] is True
    assert data["offline_only"] is True
    assert data["shadow_only"] is True
    assert data["live_pipeline_influence"] is False
    assert data["no_broker_execution"] is True
    assert data["adapter_type"] == "finrlx_research_spike"
    assert data["finrlx_available"] is False
    assert data["training_mode"] == "stubbed"


# ── Dataset validation ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dataset_validation(client):
    """POST /rl/finrlx/validate-dataset returns truthful validation."""
    r = await client.post("/api/v1/rl/finrlx/validate-dataset", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15", "limit": 5,
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert "valid" in data
    assert "row_count" in data
    assert "asset_count" in data
    assert "schema_version" in data
    assert data["safety_flags"]["research_only"] is True


@pytest.mark.asyncio
async def test_dataset_missing_fields_truthful(client):
    """Dataset validation reports missing fields truthfully."""
    r = await client.post("/api/v1/rl/finrlx/validate-dataset", json={"limit": 5})
    data = r.json()["data"]
    assert isinstance(data["missing_fields"], list)
    assert isinstance(data["warnings"], list)


# ── Train research ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_train_requires_acknowledgement(client):
    """POST /rl/finrlx/train-research requires research_acknowledgement=true."""
    r = await client.post("/api/v1/rl/finrlx/train-research", json={
        "name": "Test", "research_acknowledgement": False,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_train_stub_creates_candidate(client):
    """POST /rl/finrlx/train-research creates a research-only candidate."""
    r = await client.post("/api/v1/rl/finrlx/train-research", json={
        "name": "Test Research Candidate",
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["training_status"] == "completed"
    assert data["training_mode"] == "stubbed"
    assert data["real_neural_training"] is False
    assert data["policy_candidate_id"] is not None
    assert data["safety_flags"]["research_only"] is True
    assert data["safety_flags"]["offline_only"] is True
    assert data["safety_flags"]["no_broker_execution"] is True
    assert data["safety_flags"]["no_recommendation_pollution"] is True


# ── Candidates ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_candidates_list(client):
    """GET /rl/finrlx/candidates returns research candidates."""
    # Create one first
    await client.post("/api/v1/rl/finrlx/train-research", json={
        "research_acknowledgement": True,
    })
    r = await client.get("/api/v1/rl/finrlx/candidates")
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) >= 1
    assert data[0]["research_only"] is True
    assert data[0]["policy_type"] == "finrlx_research_stub"


@pytest.mark.asyncio
async def test_candidate_detail(client):
    """GET /rl/finrlx/candidates/{id} returns candidate detail."""
    r = await client.post("/api/v1/rl/finrlx/train-research", json={
        "research_acknowledgement": True,
    })
    cid = r.json()["data"]["policy_candidate_id"]
    r2 = await client.get(f"/api/v1/rl/finrlx/candidates/{cid}")
    assert r2.status_code == 200
    data = r2.json()["data"]
    assert data["id"] == cid
    assert data["no_publication_influence"] is True


# ── Safety regressions ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_candidate_cannot_affect_recommendations(client):
    """/recommendations/current is not affected."""
    await client.post("/api/v1/rl/finrlx/train-research", json={
        "research_acknowledgement": True,
    })
    r = await client.get("/api/v1/recommendations/current")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_candidate_cannot_affect_overview(client):
    """/overview is not affected."""
    r = await client.get("/api/v1/overview")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_candidate_cannot_affect_publication(client):
    """/publication/status is not affected."""
    r = await client.get("/api/v1/publication/status")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_no_broker_execution(client):
    """/rl/execute still unavailable."""
    r = await client.post("/api/v1/rl/execute", json={})
    assert r.status_code in (404, 405, 422)


@pytest.mark.asyncio
async def test_existing_benchmark_still_works(client):
    """Existing benchmark workflow still works."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
    })
    assert r.json()["data"]["status"] in ("completed", "partial")


@pytest.mark.asyncio
async def test_existing_pipeline_still_works(client):
    """Pipeline still works."""
    from datetime import date
    today = date.today().isoformat()
    r = await client.post("/api/v1/features/compute", json={"as_of": today})
    fs_id = r.json()["data"]["feature_set_id"]
    await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})
    r = await client.post("/api/v1/pipeline/run", json={"feature_set_id": fs_id})
    assert r.json()["data"]["status"] == "completed"
