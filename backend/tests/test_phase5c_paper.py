"""Phase 5C tests: paper portfolio realization."""
import pytest


async def _ensure_published(client) -> str:
    """Ensure a published recommendation exists. Returns rec_id."""
    from datetime import date
    today = date.today().isoformat()
    r = await client.post("/api/v1/features/compute", json={"as_of": today})
    fs_id = r.json()["data"]["feature_set_id"]
    await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})
    r = await client.post("/api/v1/pipeline/run", json={"feature_set_id": fs_id})
    rec_id = r.json()["data"]["recommendation_id"]
    # Stage → approve → publish
    await client.post(f"/api/v1/publication/recommendations/{rec_id}/stage", json={"actor": "test"})
    await client.post(f"/api/v1/publication/recommendations/{rec_id}/approve", json={"actor": "test"})
    await client.post(f"/api/v1/publication/recommendations/{rec_id}/publish", json={"actor": "test"})
    return rec_id


async def _ensure_draft(client) -> str:
    """Ensure a draft recommendation exists. Returns rec_id."""
    from datetime import date
    today = date.today().isoformat()
    r = await client.post("/api/v1/features/compute", json={"as_of": today})
    fs_id = r.json()["data"]["feature_set_id"]
    await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})
    r = await client.post("/api/v1/pipeline/run", json={"feature_set_id": fs_id})
    return r.json()["data"]["recommendation_id"]


# ── Provenance ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_seeded_paper_labeled_demo(client):
    """Seeded paper portfolio from conftest is labeled seed_demo/unknown."""
    r = await client.get("/api/v1/paper/current")
    assert r.status_code == 200
    data = r.json()["data"]
    if data is not None:
        assert data["source_type"] in ("seed_demo", "unknown")
        assert data["is_demo"] is True


# ── Create from recommendation ────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_from_published(client):
    """Paper portfolio can be created from a published recommendation."""
    rec_id = await _ensure_published(client)
    # The publish may be blocked by incidents/breaches in test DB
    # Check if we actually got published
    r = await client.get(f"/api/v1/recommendations/{rec_id}")
    rec_status = r.json()["data"]["status"]
    if rec_status not in ("published", "published_with_warning"):
        pytest.skip("Could not publish (blocked by test DB incidents/breaches)")

    r = await client.post(f"/api/v1/paper/from-recommendation/{rec_id}", json={})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["source_type"] == "recommendation_paper"
    assert data["is_demo"] is False
    assert data["source_recommendation_id"] == rec_id
    assert len(data["holdings"]) >= 1


@pytest.mark.asyncio
async def test_create_from_draft_rejected(client):
    """Paper portfolio from draft recommendation is rejected by default."""
    rec_id = await _ensure_draft(client)
    r = await client.post(f"/api/v1/paper/from-recommendation/{rec_id}", json={})
    assert r.status_code == 400  # rejected


@pytest.mark.asyncio
async def test_create_from_draft_with_flag(client):
    """Paper portfolio from draft allowed with allow_unpublished=true, marked test."""
    rec_id = await _ensure_draft(client)
    r = await client.post(f"/api/v1/paper/from-recommendation/{rec_id}",
                          json={"allow_unpublished": True})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["source_type"] == "test_paper"
    assert data["source_recommendation_id"] == rec_id


# ── Holdings ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_holdings_from_recommendation(client):
    """Created portfolio has holdings matching recommendation weights."""
    rec_id = await _ensure_draft(client)
    r = await client.post(f"/api/v1/paper/from-recommendation/{rec_id}",
                          json={"allow_unpublished": True})
    data = r.json()["data"]
    assert len(data["holdings"]) >= 1
    for h in data["holdings"]:
        assert "target_weight" in h
        assert "current_weight" in h
        assert "ticker" in h


# ── Drift ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_drift_endpoint(client):
    """Drift endpoint computes drift from current market prices."""
    rec_id = await _ensure_draft(client)
    r = await client.post(f"/api/v1/paper/from-recommendation/{rec_id}",
                          json={"allow_unpublished": True})
    pp_id = r.json()["data"]["id"]

    r2 = await client.get(f"/api/v1/paper/{pp_id}/drift")
    assert r2.status_code == 200
    data = r2.json()["data"]
    assert "total_value" in data
    assert "drift_count" in data
    assert "max_drift" in data


# ── Events ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_events_endpoint(client):
    """Events endpoint returns paper portfolio events."""
    rec_id = await _ensure_draft(client)
    r = await client.post(f"/api/v1/paper/from-recommendation/{rec_id}",
                          json={"allow_unpublished": True})
    pp_id = r.json()["data"]["id"]

    r2 = await client.get(f"/api/v1/paper/{pp_id}/events")
    assert r2.status_code == 200
    events = r2.json()["data"]
    assert len(events) >= 1
    assert events[0]["event_type"] == "creation"


# ── List ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_paper_list(client):
    """GET /paper returns all paper portfolios."""
    r = await client.get("/api/v1/paper")
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) >= 1
    for p in data:
        assert "source_type" in p
        assert "is_demo" in p
