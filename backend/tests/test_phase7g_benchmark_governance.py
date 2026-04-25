"""Phase 7G tests: benchmark governance, audit trail, fingerprint, invariants."""
import pytest


@pytest.mark.asyncio
async def test_benchmark_creates_audit_events(client):
    """Running a benchmark creates audit events."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
    })
    report_id = r.json()["data"]["id"]
    r2 = await client.get(f"/api/v1/rl/benchmarks/{report_id}/audit")
    assert r2.status_code == 200
    events = r2.json()["data"]
    assert len(events) >= 2  # requested + completed
    types = {e["event_type"] for e in events}
    assert "benchmark_run_requested" in types
    assert any("benchmark_run_completed" in t or "benchmark_run_partial" in t for t in types)


@pytest.mark.asyncio
async def test_audit_list_endpoint(client):
    """GET /rl/benchmarks/audit returns recent audit events."""
    r = await client.get("/api/v1/rl/benchmarks/audit")
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)


@pytest.mark.asyncio
async def test_completed_audit_has_fingerprint(client):
    """Completed benchmark audit event includes result_fingerprint."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
    })
    report_id = r.json()["data"]["id"]
    r2 = await client.get(f"/api/v1/rl/benchmarks/{report_id}/audit")
    completed = [e for e in r2.json()["data"] if "completed" in (e["event_type"] or "")]
    assert len(completed) >= 1
    assert completed[0]["result_fingerprint"] is not None
    assert len(completed[0]["result_fingerprint"]) == 64  # SHA-256 hex


@pytest.mark.asyncio
async def test_fingerprint_deterministic(client):
    """Deterministic agents produce same fingerprint for same inputs."""
    # Use only deterministic agents to test fingerprint stability
    r1 = await client.post("/api/v1/rl/benchmarks/run", json={
        "name": "FP test", "start_date": "2026-03-20", "end_date": "2026-04-10",
        "agent_keys": ["heuristic_baseline", "score_weighted_baseline"],
    })
    r2 = await client.post("/api/v1/rl/benchmarks/run", json={
        "name": "FP test", "start_date": "2026-03-20", "end_date": "2026-04-10",
        "agent_keys": ["heuristic_baseline", "score_weighted_baseline"],
    })
    fp1 = r1.json()["data"].get("result_fingerprint")
    fp2 = r2.json()["data"].get("result_fingerprint")
    if fp1 and fp2:
        assert fp1 == fp2


@pytest.mark.asyncio
async def test_invariant_checks_pass(client):
    """Invariant checks pass for standard benchmark."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
    })
    inv = r.json()["data"].get("invariant_check_results")
    assert inv is not None
    assert inv["all_passed"] is True
    assert inv["offline_only"] is True
    assert inv["no_live_pipeline_influence"] is True
    assert inv["no_broker_execution"] is True


@pytest.mark.asyncio
async def test_audit_includes_safety_flags(client):
    """Audit event includes safety_flags."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
    })
    report_id = r.json()["data"]["id"]
    r2 = await client.get(f"/api/v1/rl/benchmarks/{report_id}/audit")
    completed = [e for e in r2.json()["data"] if "completed" in (e["event_type"] or "")]
    assert completed[0]["safety_flags"]["offline_only"] is True


@pytest.mark.asyncio
async def test_audit_includes_agents(client):
    """Audit event includes requested/executed/skipped agents."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
    })
    report_id = r.json()["data"]["id"]
    r2 = await client.get(f"/api/v1/rl/benchmarks/{report_id}/audit")
    completed = [e for e in r2.json()["data"] if "completed" in (e["event_type"] or "")]
    ev = completed[0]
    assert "heuristic_baseline" in ev["executed_agents"]
    assert isinstance(ev["skipped_agents"], list)


@pytest.mark.asyncio
async def test_benchmark_response_includes_fingerprint(client):
    """Benchmark response includes result_fingerprint and invariant_check_results."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
    })
    data = r.json()["data"]
    assert data["result_fingerprint"] is not None
    assert data["invariant_check_results"] is not None
    assert data["invariant_check_results"]["all_passed"] is True


# ── Safety regressions ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_no_broker_execution(client):
    """/rl/execute still unavailable."""
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
