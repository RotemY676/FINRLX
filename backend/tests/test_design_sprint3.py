"""Design Sprint 3 tests: ops DB-backed endpoints, sub-endpoints, queue actions, workspace counts."""
import pytest


@pytest.mark.asyncio
async def test_ops_full(client):
    """GET /ops returns all 7 sections including system_kpis."""
    r = await client.get("/api/v1/ops")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "queue" in data
    assert "feeds" in data
    assert "engines" in data
    assert "breaches" in data
    assert "incidents" in data
    assert "audit" in data
    assert "system_kpis" in data
    assert len(data["system_kpis"]) == 6
    assert len(data["feeds"]) >= 2
    assert len(data["breaches"]) >= 2
    assert len(data["queue"]) >= 2


@pytest.mark.asyncio
async def test_ops_queue_sub(client):
    """GET /ops/queue returns pending queue items."""
    r = await client.get("/api/v1/ops/queue")
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_ops_queue_filter_high(client):
    """GET /ops/queue?filter=high returns only high-priority items."""
    r = await client.get("/api/v1/ops/queue?filter=high")
    assert r.status_code == 200
    data = r.json()["data"]
    for item in data:
        assert item["priority"] == "high"


@pytest.mark.asyncio
async def test_ops_feeds_sub(client):
    """GET /ops/feeds returns data feeds."""
    r = await client.get("/api/v1/ops/feeds")
    assert r.status_code == 200
    assert len(r.json()["data"]) >= 2


@pytest.mark.asyncio
async def test_ops_engines_sub(client):
    """GET /ops/engines returns engine health computed from signal_runs."""
    r = await client.get("/api/v1/ops/engines")
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) >= 1
    assert "latency" in data[0]
    assert "status" in data[0]


@pytest.mark.asyncio
async def test_ops_breaches_sub(client):
    """GET /ops/breaches returns active breaches."""
    r = await client.get("/api/v1/ops/breaches")
    assert r.status_code == 200
    assert len(r.json()["data"]) >= 2


@pytest.mark.asyncio
async def test_ops_incidents_sub(client):
    """GET /ops/incidents returns open incidents."""
    r = await client.get("/api/v1/ops/incidents")
    assert r.status_code == 200
    assert len(r.json()["data"]) >= 1


@pytest.mark.asyncio
async def test_ops_audit_sub(client):
    """GET /ops/audit returns audit entries."""
    r = await client.get("/api/v1/ops/audit")
    assert r.status_code == 200
    assert len(r.json()["data"]) >= 2


@pytest.mark.asyncio
async def test_ops_audit_scope_filter(client):
    """GET /ops/audit?scope=recommendation filters by scope."""
    r = await client.get("/api/v1/ops/audit?scope=recommendation")
    assert r.status_code == 200
    data = r.json()["data"]
    for entry in data:
        assert entry["scope"] == "recommendation"


@pytest.mark.asyncio
async def test_workspace_counts(client):
    """GET /workspace-counts returns counts for sidebar badges."""
    r = await client.get("/api/v1/workspace-counts")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "overview" in data
    assert "decisions" in data
    assert "risk" in data
    assert "ops" in data
    assert data["overview"] >= 2  # 2 pending queue items
    assert data["risk"] >= 2  # 2 active breaches
    assert data["ops"] >= 1  # 1 open incident


@pytest.mark.asyncio
async def test_queue_approve_action(client):
    """POST /ops/queue/{id}/approve changes item status."""
    # First get queue to find an item id
    r = await client.get("/api/v1/ops/queue")
    items = r.json()["data"]
    assert len(items) > 0
    item_id = items[0]["id"]

    r = await client.post(f"/api/v1/ops/queue/{item_id}/approve")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["new_status"] == "approved"


@pytest.mark.asyncio
async def test_queue_action_404(client):
    """POST /ops/queue/{bad_id}/defer returns 404."""
    r = await client.post("/api/v1/ops/queue/nonexistent-id/defer")
    assert r.status_code == 404
