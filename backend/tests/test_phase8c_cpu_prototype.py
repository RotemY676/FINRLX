"""Phase 8C tests: CPU-only PPO/A2C offline prototype."""
import pytest


# ── Dependencies ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dependencies_endpoint(client):
    """GET /rl/finrlx/dependencies works even when optional deps missing."""
    r = await client.get("/api/v1/rl/finrlx/dependencies")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "numpy_available" in data
    assert "gymnasium_available" in data
    assert "stable_baselines3_available" in data
    assert "torch_available" in data
    assert data["cpu_only_mode"] is True
    assert "neural_training_available" in data
    assert "missing_dependencies" in data


@pytest.mark.asyncio
async def test_app_boots_without_neural_deps(client):
    """App still works when neural dependencies are absent."""
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    r2 = await client.get("/api/v1/rl/finrlx/status")
    assert r2.status_code == 200


# ── Train CPU prototype ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cpu_prototype_requires_acknowledgement(client):
    """train-cpu-prototype requires research_acknowledgement=true."""
    r = await client.post("/api/v1/rl/finrlx/train-cpu-prototype", json={
        "algorithm": "PPO", "research_acknowledgement": False,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_cpu_prototype_validates_algorithm(client):
    """train-cpu-prototype rejects invalid algorithm."""
    r = await client.post("/api/v1/rl/finrlx/train-cpu-prototype", json={
        "algorithm": "INVALID", "research_acknowledgement": True,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_cpu_prototype_rejects_excessive_timesteps(client):
    """train-cpu-prototype rejects timesteps > 500."""
    r = await client.post("/api/v1/rl/finrlx/train-cpu-prototype", json={
        "algorithm": "PPO", "timesteps": 1000, "research_acknowledgement": True,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_cpu_prototype_runs(client):
    """train-cpu-prototype runs and returns truthful status."""
    r = await client.post("/api/v1/rl/finrlx/train-cpu-prototype", json={
        "name": "Test CPU Prototype",
        "algorithm": "PPO",
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "timesteps": 50, "seed": 42,
        "research_acknowledgement": True,
    })
    assert r.status_code == 200
    data = r.json()["data"]
    # Must be one of: completed (real training), dependency_unavailable, failed
    assert data["status"] in ("completed", "dependency_unavailable", "failed")
    assert data["safety_flags"]["research_only"] is True
    assert data["safety_flags"]["no_broker_execution"] is True
    assert data["not_eligible_for_promotion"] is True

    # If dependencies unavailable, training_mode must be truthful
    if data["status"] == "dependency_unavailable":
        assert data["real_neural_training"] is False
        assert data["training_mode"] == "dependency_unavailable"
        assert len(data.get("dependency_status", {}).get("missing_dependencies", [])) > 0


@pytest.mark.asyncio
async def test_cpu_prototype_creates_candidate(client):
    """CPU prototype creates a candidate even when dependencies unavailable."""
    r = await client.post("/api/v1/rl/finrlx/train-cpu-prototype", json={
        "algorithm": "A2C", "timesteps": 30, "research_acknowledgement": True,
    })
    data = r.json()["data"]
    assert data["policy_candidate_id"] is not None

    # Candidate should be accessible
    cid = data["policy_candidate_id"]
    r2 = await client.get(f"/api/v1/rl/finrlx/candidates/{cid}")
    assert r2.status_code == 200
    assert r2.json()["data"]["safety_flags"]["research_only"] is True


@pytest.mark.asyncio
async def test_cpu_prototype_isolation(client):
    """CPU prototype candidate passes isolation checks."""
    r = await client.post("/api/v1/rl/finrlx/train-cpu-prototype", json={
        "algorithm": "PPO", "research_acknowledgement": True,
    })
    cid = r.json()["data"]["policy_candidate_id"]
    r2 = await client.get(f"/api/v1/rl/finrlx/candidates/{cid}/isolation")
    assert r2.status_code == 200
    assert r2.json()["data"]["all_blocked"] is True


@pytest.mark.asyncio
async def test_cpu_prototype_fingerprints(client):
    """CPU prototype captures production fingerprints."""
    r = await client.post("/api/v1/rl/finrlx/train-cpu-prototype", json={
        "algorithm": "PPO", "research_acknowledgement": True,
    })
    fp = r.json()["data"]["production_fingerprints"]
    assert "component_checks" in fp
    assert "recommendations_current" in fp["component_checks"]
    assert "publication_status" in fp["component_checks"]
    assert "overview" in fp["component_checks"]


@pytest.mark.asyncio
async def test_cpu_prototype_audit(client):
    """CPU prototype creates audit events."""
    from tests.conftest import test_session_factory
    from sqlalchemy import select
    from app.models.ops import AuditEvent

    await client.post("/api/v1/rl/finrlx/train-cpu-prototype", json={
        "algorithm": "PPO", "research_acknowledgement": True,
    })

    async with test_session_factory() as db:
        events = (await db.execute(
            select(AuditEvent)
            .where(AuditEvent.object_type == "finrlx_research")
            .where(AuditEvent.action.like("finrlx_cpu_%"))
            .order_by(AuditEvent.occurred_at.desc())
        )).scalars().all()

    assert len(events) >= 2  # requested + completed/unavailable/failed
    actions = {e.action for e in events}
    assert "finrlx_cpu_research_train_requested" in actions


# ── Safety regressions ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_no_broker_execution(client):
    r = await client.post("/api/v1/rl/execute", json={})
    assert r.status_code in (404, 405, 422)


@pytest.mark.asyncio
async def test_recommendations_unaffected(client):
    r = await client.get("/api/v1/recommendations/current")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_overview_unaffected(client):
    r = await client.get("/api/v1/overview")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_publication_unaffected(client):
    r = await client.get("/api/v1/publication/status")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_existing_benchmark_still_works(client):
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
    })
    assert r.json()["data"]["status"] in ("completed", "partial")


@pytest.mark.asyncio
async def test_phase8a_8b_endpoints_still_work(client):
    r = await client.get("/api/v1/rl/finrlx/status")
    assert r.status_code == 200
    r2 = await client.post("/api/v1/rl/finrlx/validate-dataset", json={"limit": 3})
    assert r2.status_code == 200
    r3 = await client.post("/api/v1/rl/finrlx/train-research", json={
        "research_acknowledgement": True,
    })
    assert r3.json()["data"]["training_status"] == "completed"
