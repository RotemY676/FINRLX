"""Phase 8B tests: FinRL-X research safety hardening and candidate isolation."""
import pytest


# ── Candidate isolation ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_isolation_endpoint_blocks_all(client):
    """GET /rl/finrlx/candidates/{id}/isolation blocks all unsafe actions."""
    r = await client.post("/api/v1/rl/finrlx/train-research", json={
        "research_acknowledgement": True,
    })
    cid = r.json()["data"]["policy_candidate_id"]
    r2 = await client.get(f"/api/v1/rl/finrlx/candidates/{cid}/isolation")
    assert r2.status_code == 200
    data = r2.json()["data"]
    assert data["isolated"] is True
    assert data["all_blocked"] is True
    assert data["checks"]["promotion_blocked"] is True
    assert data["checks"]["publication_blocked"] is True
    assert data["checks"]["live_recommendation_blocked"] is True
    assert data["checks"]["overview_influence_blocked"] is True
    assert data["checks"]["broker_execution_blocked"] is True


@pytest.mark.asyncio
async def test_isolation_includes_safety_flags(client):
    """Isolation response includes safety_flags."""
    r = await client.post("/api/v1/rl/finrlx/train-research", json={
        "research_acknowledgement": True,
    })
    cid = r.json()["data"]["policy_candidate_id"]
    r2 = await client.get(f"/api/v1/rl/finrlx/candidates/{cid}/isolation")
    sf = r2.json()["data"]["safety_flags"]
    assert sf["research_only"] is True
    assert sf["offline_only"] is True
    assert sf["no_broker_execution"] is True


# ── Safety flags consistency ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_train_response_includes_safety_flags(client):
    """Train response includes safety_flags object."""
    r = await client.post("/api/v1/rl/finrlx/train-research", json={
        "research_acknowledgement": True,
    })
    sf = r.json()["data"]["safety_flags"]
    assert sf["research_only"] is True
    assert sf["no_recommendation_pollution"] is True


@pytest.mark.asyncio
async def test_candidate_detail_includes_safety_flags(client):
    """Candidate detail includes safety_flags."""
    r = await client.post("/api/v1/rl/finrlx/train-research", json={
        "research_acknowledgement": True,
    })
    cid = r.json()["data"]["policy_candidate_id"]
    r2 = await client.get(f"/api/v1/rl/finrlx/candidates/{cid}")
    assert "safety_flags" in r2.json()["data"]
    assert r2.json()["data"]["safety_flags"]["research_only"] is True


@pytest.mark.asyncio
async def test_candidate_list_includes_safety_flags(client):
    """Candidate list items include safety_flags."""
    await client.post("/api/v1/rl/finrlx/train-research", json={
        "research_acknowledgement": True,
    })
    r = await client.get("/api/v1/rl/finrlx/candidates")
    assert len(r.json()["data"]) >= 1
    assert "safety_flags" in r.json()["data"][0]


# ── Audit events ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_train_creates_audit_events_persisted(client):
    """Train-research creates persisted requested + completed audit events in DB."""
    from tests.conftest import test_session_factory
    from sqlalchemy import select
    from app.models.ops import AuditEvent

    r = await client.post("/api/v1/rl/finrlx/train-research", json={
        "research_acknowledgement": True,
        "start_date": "2026-03-15", "end_date": "2026-04-15",
    })
    assert r.json()["data"]["training_status"] == "completed"
    candidate_id = r.json()["data"]["policy_candidate_id"]

    # Query DB directly for finrlx_research audit events
    async with test_session_factory() as db:
        events = (await db.execute(
            select(AuditEvent)
            .where(AuditEvent.object_type == "finrlx_research")
            .order_by(AuditEvent.occurred_at.desc())
        )).scalars().all()

    actions = {e.action for e in events}
    assert "finrlx_train_research_requested" in actions
    assert "finrlx_train_research_completed" in actions

    # Verify requested event details
    requested = next(e for e in events if e.action == "finrlx_train_research_requested")
    rd = requested.details or {}
    assert rd.get("research_acknowledgement") is True
    assert rd.get("safety_flags", {}).get("research_only") is True
    assert rd.get("name") is not None

    # Verify completed event details
    completed = next(e for e in events if e.action == "finrlx_train_research_completed")
    cd = completed.details or {}
    assert cd.get("candidate_id") is not None
    assert cd.get("training_run_id") is not None
    assert cd.get("safety_flags", {}).get("research_only") is True
    assert cd.get("isolation_checks", {}).get("promotion_blocked") is True
    assert "production_fingerprints_unchanged" in cd

    # Verify component_checks in completed audit event
    cc = cd.get("component_checks", {})
    assert "recommendations_current" in cc
    assert "publication_status" in cc
    assert "overview" in cc
    assert cc["recommendations_current"].get("snapshot_available") is True
    assert cc["publication_status"].get("snapshot_available") is True
    assert cc["overview"].get("snapshot_available") is False
    assert cc["overview"].get("reason") is not None


@pytest.mark.asyncio
async def test_production_fingerprints_components(client):
    """Train-research includes per-component production fingerprints."""
    r = await client.post("/api/v1/rl/finrlx/train-research", json={
        "research_acknowledgement": True,
    })
    fp = r.json()["data"]["production_fingerprints"]
    assert fp is not None

    # Must have all three component keys
    assert "recommendations_current" in fp["before"]
    assert "publication_status" in fp["before"]
    assert "overview" in fp["before"]

    # component_checks must exist for all three
    cc = fp["component_checks"]
    assert "recommendations_current" in cc
    assert "publication_status" in cc
    assert "overview" in cc

    # recommendations_current should be available and unchanged
    rc = cc["recommendations_current"]
    assert rc["snapshot_available"] is True
    assert rc["unchanged"] is True

    # publication_status should be available and unchanged
    ps = cc["publication_status"]
    assert ps["snapshot_available"] is True
    assert ps["unchanged"] is True

    # overview should be unavailable with reason
    ov = cc["overview"]
    assert ov["snapshot_available"] is False
    assert ov["unchanged"] is None
    assert "reason" in ov

    # overall unchanged: true (available components unchanged)
    assert fp["unchanged"] is True


# ── Acknowledgement ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_missing_acknowledgement_still_rejected(client):
    """Missing research_acknowledgement still returns 422."""
    r = await client.post("/api/v1/rl/finrlx/train-research", json={
        "research_acknowledgement": False,
    })
    assert r.status_code == 422


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
async def test_phase8a_endpoints_still_work(client):
    """Phase 8A endpoints still work."""
    r = await client.get("/api/v1/rl/finrlx/status")
    assert r.status_code == 200
    r2 = await client.post("/api/v1/rl/finrlx/validate-dataset", json={"limit": 3})
    assert r2.status_code == 200
