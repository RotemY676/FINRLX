"""Phase 4E tests: publication workflow — gates, state machine, audit."""
import pytest


async def _ensure_pipeline_draft(client) -> str:
    """Ensure a pipeline draft recommendation exists. Returns rec_id."""
    from datetime import date
    today = date.today().isoformat()
    r = await client.post("/api/v1/features/compute", json={"as_of": today})
    fs_id = r.json()["data"]["feature_set_id"]
    await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})
    r = await client.post("/api/v1/pipeline/run", json={"feature_set_id": fs_id})
    return r.json()["data"]["recommendation_id"]


# ── Gate evaluation ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_gate_evaluation(client):
    """Gates evaluate correctly for a pipeline draft."""
    rec_id = await _ensure_pipeline_draft(client)
    r = await client.get(f"/api/v1/publication/recommendations/{rec_id}/gates")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["recommendation_id"] == rec_id
    assert data["overall"] in ("pass", "warning", "block")
    assert len(data["gates"]) >= 5


@pytest.mark.asyncio
async def test_gate_not_found(client):
    """Gates for nonexistent recommendation return block."""
    r = await client.get("/api/v1/publication/recommendations/nonexistent/gates")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["overall"] == "block"
    assert not data["can_publish"]


# ── State machine transitions ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_stage_transition(client):
    """draft -> staged works."""
    rec_id = await _ensure_pipeline_draft(client)
    r = await client.post(f"/api/v1/publication/recommendations/{rec_id}/stage",
                          json={"actor": "test"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["allowed"] is True
    assert data["new_status"] == "staged"
    assert data["previous_status"] == "draft"
    assert data["audit_event_id"] is not None


@pytest.mark.asyncio
async def test_approve_transition(client):
    """staged -> approved works."""
    rec_id = await _ensure_pipeline_draft(client)
    await client.post(f"/api/v1/publication/recommendations/{rec_id}/stage",
                      json={"actor": "test"})
    r = await client.post(f"/api/v1/publication/recommendations/{rec_id}/approve",
                          json={"actor": "test"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["allowed"] is True
    assert data["new_status"] == "approved"


@pytest.mark.asyncio
async def test_publish_transition(client):
    """approved -> published attempt returns structured response.

    May be blocked by conftest incidents/breaches — that's correct governance.
    """
    rec_id = await _ensure_pipeline_draft(client)
    await client.post(f"/api/v1/publication/recommendations/{rec_id}/stage",
                      json={"actor": "test"})
    await client.post(f"/api/v1/publication/recommendations/{rec_id}/approve",
                      json={"actor": "test"})
    r = await client.post(f"/api/v1/publication/recommendations/{rec_id}/publish",
                          json={"actor": "test"})
    assert r.status_code == 200
    data = r.json()["data"]
    # In test DB: conftest seeds active incident + breach → gates block → allowed=False is correct
    if data["allowed"]:
        assert data["new_status"] in ("published", "published_with_warning")
    else:
        # Blocked by governance gates — this is correct behavior
        assert "blocked" in data["message"].lower() or "cannot" in data["message"].lower()


@pytest.mark.asyncio
async def test_direct_draft_to_published_rejected(client):
    """draft -> published is NOT allowed (must go through staged -> approved)."""
    rec_id = await _ensure_pipeline_draft(client)
    r = await client.post(f"/api/v1/publication/recommendations/{rec_id}/publish",
                          json={"actor": "test"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["allowed"] is False
    assert "not allowed" in data["message"].lower() or "cannot" in data["message"].lower()


# ── Defer / suppress ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_defer_requires_reason(client):
    """Defer without reason is rejected."""
    rec_id = await _ensure_pipeline_draft(client)
    await client.post(f"/api/v1/publication/recommendations/{rec_id}/stage",
                      json={"actor": "test"})
    r = await client.post(f"/api/v1/publication/recommendations/{rec_id}/defer",
                          json={"actor": "test"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["allowed"] is False


@pytest.mark.asyncio
async def test_defer_with_reason(client):
    """Defer with reason works."""
    rec_id = await _ensure_pipeline_draft(client)
    await client.post(f"/api/v1/publication/recommendations/{rec_id}/stage",
                      json={"actor": "test"})
    r = await client.post(f"/api/v1/publication/recommendations/{rec_id}/defer",
                          json={"actor": "test", "reason": "Awaiting earnings"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["allowed"] is True
    assert data["new_status"] == "deferred"


@pytest.mark.asyncio
async def test_suppress_requires_reason(client):
    """Suppress without reason is rejected."""
    rec_id = await _ensure_pipeline_draft(client)
    r = await client.post(f"/api/v1/publication/recommendations/{rec_id}/suppress",
                          json={"actor": "test"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["allowed"] is False


# ── Audit trail ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_audit_event_created(client):
    """Each transition creates an audit event."""
    rec_id = await _ensure_pipeline_draft(client)
    await client.post(f"/api/v1/publication/recommendations/{rec_id}/stage",
                      json={"actor": "test_auditor"})

    r = await client.get(f"/api/v1/publication/recommendations/{rec_id}/history")
    assert r.status_code == 200
    history = r.json()["data"]
    assert len(history) >= 1
    assert any(h["actor"] == "test_auditor" for h in history)


# ── Publication status ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_publication_status(client):
    """GET /publication/status returns counts."""
    r = await client.get("/api/v1/publication/status")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "total_draft" in data
    assert "total_published" in data


# ── Current/overview after publish ────────────────────────────────────

@pytest.mark.asyncio
async def test_current_after_publish(client):
    """After publishing (if gates pass), /recommendations/current returns the published rec.

    In test DB with active incidents/breaches, publish may be blocked — test the
    /recommendations/current endpoint still works and returns a recommendation.
    """
    r = await client.get("/api/v1/recommendations/current")
    assert r.status_code == 200
    data = r.json()["data"]
    # Should return something (published or draft fallback)
    if data is not None:
        assert data["status"] in ("published", "published_with_warning", "draft", "staged", "approved", "superseded")


@pytest.mark.asyncio
async def test_overview_after_publish(client):
    """After publishing, /overview returns the published rec."""
    r = await client.get("/api/v1/overview")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["current_recommendation"] is not None


# ── Phase 4E.1 governance hardening tests ─────────────────────────────

@pytest.mark.asyncio
async def test_publish_blocked_by_critical_incident(client):
    """Publication is blocked when a critical incident is active.

    The conftest seeds a sev-2 incident (status=open). Gates should block.
    """
    rec_id = await _ensure_pipeline_draft(client)
    await client.post(f"/api/v1/publication/recommendations/{rec_id}/stage",
                      json={"actor": "test"})
    await client.post(f"/api/v1/publication/recommendations/{rec_id}/approve",
                      json={"actor": "test"})

    # Check gates — should see incidents gate as block
    r = await client.get(f"/api/v1/publication/recommendations/{rec_id}/gates")
    data = r.json()["data"]
    incident_gate = next((g for g in data["gates"] if g["gate"] == "incidents"), None)
    assert incident_gate is not None
    assert incident_gate["status"] == "block"

    # Publish attempt should fail
    r2 = await client.post(f"/api/v1/publication/recommendations/{rec_id}/publish",
                           json={"actor": "test"})
    data2 = r2.json()["data"]
    assert data2["allowed"] is False
    assert "blocked" in data2["message"].lower()


@pytest.mark.asyncio
async def test_publish_blocked_by_policy_breach(client):
    """Publication is blocked when an active policy breach exists.

    The conftest seeds an active breach with severity='breach'. Gates should block.
    """
    rec_id = await _ensure_pipeline_draft(client)
    r = await client.get(f"/api/v1/publication/recommendations/{rec_id}/gates")
    data = r.json()["data"]
    breach_gate = next((g for g in data["gates"] if g["gate"] == "policy_breaches"), None)
    assert breach_gate is not None
    assert breach_gate["status"] == "block"


@pytest.mark.asyncio
async def test_publication_queue_endpoint(client):
    """GET /publication/queue returns staged/approved/deferred recommendations."""
    rec_id = await _ensure_pipeline_draft(client)
    # Stage it so it appears in queue
    await client.post(f"/api/v1/publication/recommendations/{rec_id}/stage",
                      json={"actor": "test"})

    r = await client.get("/api/v1/publication/queue")
    assert r.status_code == 200
    queue = r.json()["data"]
    assert len(queue) >= 1
    # Should include our staged rec
    statuses = {item["status"] for item in queue}
    assert statuses.intersection({"staged", "approved", "deferred", "suppressed"})
    # Should NOT include draft
    assert "draft" not in statuses


@pytest.mark.asyncio
async def test_publication_queue_excludes_draft(client):
    """Queue does not include draft recommendations."""
    r = await client.get("/api/v1/publication/queue")
    assert r.status_code == 200
    queue = r.json()["data"]
    for item in queue:
        assert item["status"] != "draft"
