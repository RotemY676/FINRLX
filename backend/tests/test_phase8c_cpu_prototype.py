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
async def test_cpu_prototype_rejects_bad_date_range(client):
    """train-cpu-prototype rejects start_date > end_date."""
    r = await client.post("/api/v1/rl/finrlx/train-cpu-prototype", json={
        "algorithm": "PPO", "start_date": "2026-04-15", "end_date": "2026-03-15",
        "research_acknowledgement": True,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_cpu_prototype_response_includes_isolation_checks(client):
    """train-cpu-prototype response includes isolation_checks."""
    r = await client.post("/api/v1/rl/finrlx/train-cpu-prototype", json={
        "algorithm": "PPO", "research_acknowledgement": True,
    })
    data = r.json()["data"]
    assert data.get("isolation_checks") is not None
    assert data["isolation_checks"]["promotion_blocked"] is True
    assert data["isolation_checks"]["publication_blocked"] is True
    assert data["isolation_checks"]["live_recommendation_blocked"] is True
    assert data["isolation_checks"]["overview_influence_blocked"] is True
    assert data["isolation_checks"]["broker_execution_blocked"] is True
    assert data["isolated"] is True
    assert data["all_blocked"] is True


@pytest.mark.asyncio
async def test_cpu_prototype_audit_persisted(client):
    """CPU prototype audit events are persisted with full details."""
    from tests.conftest import test_session_factory
    from sqlalchemy import select
    from app.models.ops import AuditEvent

    await client.post("/api/v1/rl/finrlx/train-cpu-prototype", json={
        "algorithm": "PPO", "timesteps": 30, "seed": 42,
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })

    async with test_session_factory() as db:
        events = (await db.execute(
            select(AuditEvent)
            .where(AuditEvent.object_type == "finrlx_research")
            .where(AuditEvent.action.like("finrlx_cpu_%"))
            .order_by(AuditEvent.occurred_at.desc())
        )).scalars().all()

    actions = {e.action for e in events}
    assert "finrlx_cpu_research_train_requested" in actions

    # Verify requested event details
    requested = next(e for e in events if e.action == "finrlx_cpu_research_train_requested")
    rd = requested.details or {}
    assert rd.get("algorithm") == "PPO"
    assert rd.get("timesteps") == 30
    assert rd.get("seed") == 42
    assert rd.get("safety_flags", {}).get("research_only") is True
    assert rd.get("dependency_status") is not None

    # Verify terminal event (dependency_unavailable or completed)
    terminal_actions = {"finrlx_cpu_research_train_completed",
                        "finrlx_cpu_research_train_dependency_unavailable",
                        "finrlx_cpu_research_train_failed"}
    terminal = [e for e in events if e.action in terminal_actions]
    assert len(terminal) >= 1
    td = terminal[0].details or {}
    assert td.get("safety_flags", {}).get("research_only") is True
    assert td.get("dependency_status") is not None, "terminal event must include dependency_status"
    assert td.get("component_checks") is not None
    assert "recommendations_current" in td["component_checks"]
    assert "publication_status" in td["component_checks"]
    assert "overview" in td["component_checks"]
    assert "production_fingerprints_unchanged" in td

    # For dependency_unavailable or completed, candidate and run must exist
    if terminal[0].action in ("finrlx_cpu_research_train_dependency_unavailable",
                               "finrlx_cpu_research_train_completed"):
        assert td.get("candidate_id") is not None, "terminal event must include candidate_id"
        assert td.get("training_run_id") is not None, "terminal event must include training_run_id"
        assert td.get("isolation_checks") is not None, "terminal event must include isolation_checks"
        assert td["isolation_checks"].get("promotion_blocked") is True
        assert td["isolation_checks"].get("publication_blocked") is True
        assert td["isolation_checks"].get("live_recommendation_blocked") is True
        assert td["isolation_checks"].get("overview_influence_blocked") is True
        assert td["isolation_checks"].get("broker_execution_blocked") is True


# ── Date parsing validation (Phase 8C.2) ─────────────────────────────────

@pytest.mark.asyncio
async def test_cpu_prototype_invalid_start_date(client):
    """train-cpu-prototype rejects malformed start_date with 422."""
    r = await client.post("/api/v1/rl/finrlx/train-cpu-prototype", json={
        "algorithm": "PPO", "start_date": "not-a-date",
        "research_acknowledgement": True,
    })
    assert r.status_code == 422
    assert "start_date" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cpu_prototype_invalid_end_date(client):
    """train-cpu-prototype rejects malformed end_date with 422."""
    r = await client.post("/api/v1/rl/finrlx/train-cpu-prototype", json={
        "algorithm": "PPO", "end_date": "31/12/2026",
        "research_acknowledgement": True,
    })
    assert r.status_code == 422
    assert "end_date" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_validate_dataset_invalid_start_date(client):
    """validate-dataset rejects malformed start_date with 422."""
    r = await client.post("/api/v1/rl/finrlx/validate-dataset", json={
        "start_date": "abc", "limit": 3,
    })
    assert r.status_code == 422
    assert "start_date" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_train_research_invalid_start_date(client):
    """train-research rejects malformed start_date with 422."""
    r = await client.post("/api/v1/rl/finrlx/train-research", json={
        "start_date": "xyz", "research_acknowledgement": True,
    })
    assert r.status_code == 422
    assert "start_date" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_invalid_date_does_not_create_candidate(client):
    """Malformed date input does not silently create a candidate."""
    r1 = await client.get("/api/v1/rl/finrlx/candidates")
    before_count = len(r1.json()["data"])

    await client.post("/api/v1/rl/finrlx/train-cpu-prototype", json={
        "algorithm": "PPO", "start_date": "bad",
        "research_acknowledgement": True,
    })

    r2 = await client.get("/api/v1/rl/finrlx/candidates")
    assert len(r2.json()["data"]) == before_count


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
