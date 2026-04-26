"""Phase 8F tests: imported research candidate benchmark evaluation."""
import pytest


def _sample_artifact(**overrides) -> dict:
    base = {
        "artifact_type": "finrlx_cpu_rl_research_artifact",
        "schema_version": "1.0",
        "research_only": True, "offline_only": True, "shadow_only": True,
        "not_eligible_for_promotion": True, "live_pipeline_influence": False,
        "no_broker_execution": True, "no_publication_influence": True,
        "no_recommendation_pollution": True,
        "algorithm": "PPO", "real_neural_training": True, "cpu_only": True,
        "synthetic_data": True,
        "dataset_summary": {"row_count": 60, "synthetic": True},
        "training_config": {"algorithm": "PPO", "timesteps": 200, "seed": 42},
        "training_metrics": {"timesteps": 200, "algorithm": "PPO", "seed": 42,
                             "total_reward": 0.01},
        "artifact_created_at": "2026-04-26T12:00:00Z",
        "warnings": ["Synthetic test artifact."],
    }
    base.update(overrides)
    return base


async def _import_candidate(client) -> str:
    r = await client.post("/api/v1/rl/finrlx/import-research-artifact", json={
        "artifact": _sample_artifact(),
        "import_acknowledgement": True,
        "source": "benchmark_test",
    })
    return r.json()["data"]["policy_candidate_id"]


# ── Benchmark eligibility (strengthened, Phase 8F.1 GAP 1) ──────────

@pytest.mark.asyncio
async def test_eligibility_rejects_missing_candidate(client):
    r = await client.get("/api/v1/rl/finrlx/candidates/nonexistent-id/benchmark-eligibility")
    data = r.json()["data"]
    assert data["eligible"] is False
    assert "not found" in data["reasons"][0].lower()


@pytest.mark.asyncio
async def test_eligibility_rejects_non_imported(client):
    r = await client.post("/api/v1/rl/finrlx/train-research", json={
        "research_acknowledgement": True,
    })
    cid = r.json()["data"]["policy_candidate_id"]
    r2 = await client.get(f"/api/v1/rl/finrlx/candidates/{cid}/benchmark-eligibility")
    data = r2.json()["data"]
    assert data["eligible"] is False
    assert any("not imported" in r.lower() for r in data["reasons"])


@pytest.mark.asyncio
async def test_eligibility_accepts_imported(client):
    cid = await _import_candidate(client)
    r = await client.get(f"/api/v1/rl/finrlx/candidates/{cid}/benchmark-eligibility")
    data = r.json()["data"]
    assert data["eligible"] is True
    assert data["isolation_checks"]["promotion_blocked"] is True
    assert data["isolation_checks"]["broker_execution_blocked"] is True
    assert data["candidate_summary"]["imported_from_artifact"] is True


@pytest.mark.asyncio
async def test_eligibility_checks_all_safety_flags(client):
    """Eligible imported candidate must pass all safety flag checks."""
    cid = await _import_candidate(client)
    r = await client.get(f"/api/v1/rl/finrlx/candidates/{cid}/benchmark-eligibility")
    data = r.json()["data"]
    assert data["eligible"] is True
    # Verify that a valid candidate passes all checks — reasons should be the success message
    assert "benchmark-eligible" in data["reasons"][0].lower()


# ── Candidate benchmark run ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_benchmark_requires_acknowledgement(client):
    cid = await _import_candidate(client)
    r = await client.post(f"/api/v1/rl/finrlx/candidates/{cid}/benchmark", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": False,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_benchmark_validates_malformed_dates(client):
    cid = await _import_candidate(client)
    r = await client.post(f"/api/v1/rl/finrlx/candidates/{cid}/benchmark", json={
        "start_date": "bad-date", "research_acknowledgement": True,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_benchmark_rejects_reversed_dates(client):
    cid = await _import_candidate(client)
    r = await client.post(f"/api/v1/rl/finrlx/candidates/{cid}/benchmark", json={
        "start_date": "2026-04-15", "end_date": "2026-03-15",
        "research_acknowledgement": True,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_benchmark_runs_with_baselines(client):
    cid = await _import_candidate(client)
    r = await client.post(f"/api/v1/rl/finrlx/candidates/{cid}/benchmark", json={
        "name": "8F Test Benchmark",
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "include_baselines": True,
        "research_acknowledgement": True,
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] in ("completed", "partial")
    assert data["benchmark_report_id"] is not None

    executed = data["executed_agents"]
    assert any("imported_candidate:" in a for a in executed)
    assert "heuristic_baseline" in executed or "score_weighted_baseline" in executed

    surrogate_key = [a for a in executed if "imported_candidate:" in a][0]
    assert surrogate_key in data["metrics_by_agent"]


@pytest.mark.asyncio
async def test_benchmark_include_baselines_false(client):
    """include_baselines=false runs only the imported candidate surrogate."""
    cid = await _import_candidate(client)
    r = await client.post(f"/api/v1/rl/finrlx/candidates/{cid}/benchmark", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "include_baselines": False,
        "research_acknowledgement": True,
    })
    assert r.status_code == 200
    executed = r.json()["data"]["executed_agents"]
    assert any("imported_candidate:" in a for a in executed)
    assert "heuristic_baseline" not in executed
    assert "random_valid" not in executed
    assert "score_weighted_baseline" not in executed


@pytest.mark.asyncio
async def test_benchmark_include_baselines_true_includes_all_three(client):
    """include_baselines=true includes all three baseline agents."""
    cid = await _import_candidate(client)
    r = await client.post(f"/api/v1/rl/finrlx/candidates/{cid}/benchmark", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "include_baselines": True,
        "research_acknowledgement": True,
    })
    executed = r.json()["data"]["executed_agents"]
    assert "heuristic_baseline" in executed
    assert "random_valid" in executed
    assert "score_weighted_baseline" in executed


# ── Context and truthfulness (Phase 8F.1 GAP 4) ─────────────────────

@pytest.mark.asyncio
async def test_benchmark_context_inference_mode(client):
    """candidate_benchmark_context uses truthful inference_mode."""
    cid = await _import_candidate(client)
    r = await client.post(f"/api/v1/rl/finrlx/candidates/{cid}/benchmark", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })
    ctx = r.json()["data"]["candidate_benchmark_context"]
    assert ctx["inference_mode"] == "score_weighted_fallback_surrogate"
    assert ctx["real_neural_inference"] is False
    assert ctx["artifact_metadata_used_for_inference"] is False
    assert "no neural model" in ctx["surrogate_description"].lower()
    assert ctx["not_eligible_for_promotion"] is True


@pytest.mark.asyncio
async def test_benchmark_warnings_mention_fallback(client):
    cid = await _import_candidate(client)
    r = await client.post(f"/api/v1/rl/finrlx/candidates/{cid}/benchmark", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })
    warnings = r.json()["data"]["warnings"]
    assert any("score-weighted fallback" in w.lower() for w in warnings)
    assert any("no neural" in w.lower() for w in warnings)


# ── Forensics (Phase 8F.1 GAP 2) ────────────────────────────────────

@pytest.mark.asyncio
async def test_benchmark_has_forensic_summary_by_agent(client):
    cid = await _import_candidate(client)
    r = await client.post(f"/api/v1/rl/finrlx/candidates/{cid}/benchmark", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "include_baselines": True,
        "research_acknowledgement": True,
    })
    data = r.json()["data"]
    fsa = data.get("forensic_summary_by_agent")
    assert fsa is not None
    # Should have entries for the surrogate and baselines
    assert any("imported_candidate:" in k for k in fsa.keys())


# ── Isolation and fingerprints ───────────────────────────────────────

@pytest.mark.asyncio
async def test_benchmark_has_isolation(client):
    cid = await _import_candidate(client)
    r = await client.post(f"/api/v1/rl/finrlx/candidates/{cid}/benchmark", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })
    data = r.json()["data"]
    assert data["isolation_checks"]["promotion_blocked"] is True
    assert data["isolation_checks"]["broker_execution_blocked"] is True
    assert data["all_blocked"] is True


@pytest.mark.asyncio
async def test_benchmark_has_fingerprints(client):
    cid = await _import_candidate(client)
    r = await client.post(f"/api/v1/rl/finrlx/candidates/{cid}/benchmark", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })
    fp = r.json()["data"]["production_fingerprints"]
    assert "component_checks" in fp
    assert "recommendations_current" in fp["component_checks"]


# ── Audit events ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_benchmark_audit_persisted(client):
    from tests.conftest import test_session_factory
    from sqlalchemy import select
    from app.models.ops import AuditEvent

    cid = await _import_candidate(client)
    await client.post(f"/api/v1/rl/finrlx/candidates/{cid}/benchmark", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })

    async with test_session_factory() as db:
        events = (await db.execute(
            select(AuditEvent)
            .where(AuditEvent.action.like("finrlx_candidate_benchmark_%"))
            .order_by(AuditEvent.occurred_at.desc())
        )).scalars().all()

    actions = {e.action for e in events}
    assert "finrlx_candidate_benchmark_requested" in actions
    assert "finrlx_candidate_benchmark_completed" in actions

    completed = next(e for e in events if e.action == "finrlx_candidate_benchmark_completed")
    cd = completed.details or {}
    assert cd.get("inference_mode") == "score_weighted_fallback_surrogate"
    assert cd.get("real_neural_inference") is False
    assert cd.get("artifact_metadata_used_for_inference") is False


# ── Candidate benchmark history ──────────────────────────────────────

@pytest.mark.asyncio
async def test_candidate_benchmark_history(client):
    cid = await _import_candidate(client)
    await client.post(f"/api/v1/rl/finrlx/candidates/{cid}/benchmark", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })

    r = await client.get(f"/api/v1/rl/finrlx/candidates/{cid}/benchmarks")
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) >= 1
    assert data[0]["inference_mode"] == "score_weighted_fallback_surrogate"
    assert data[0]["real_neural_inference"] is False


# ── Safety regressions ───────────────────────────────────────────────

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
async def test_existing_import_still_works(client):
    r = await client.post("/api/v1/rl/finrlx/import-research-artifact", json={
        "artifact": _sample_artifact(),
        "import_acknowledgement": True,
        "source": "regression_test",
    })
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_phase8a_8b_8c_endpoints_still_work(client):
    r = await client.get("/api/v1/rl/finrlx/status")
    assert r.status_code == 200
    r2 = await client.post("/api/v1/rl/finrlx/train-research", json={
        "research_acknowledgement": True,
    })
    assert r2.json()["data"]["training_status"] == "completed"
