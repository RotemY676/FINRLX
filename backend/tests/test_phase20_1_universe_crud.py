"""Phase 20.1 — Universe CRUD endpoints.

POST /universes        — create with unique name
PATCH /universes/{id}  — rename + toggle is_active
DELETE /universes/{id} — soft-delete (sets is_active=false)

Guardrails covered:
- duplicate name on create → 409
- rename to a name owned by a different universe → 409
- deactivating the only active universe → 409 (would brick the rest of the UI)
- mutating a non-existent id → 404
"""
import pytest


@pytest.mark.asyncio
async def test_create_universe_succeeds(client):
    r = await client.post("/api/v1/universes", json={
        "name": "Test Tech Focus",
        "description": "Narrow universe for backtesting tech-only strategies",
    })
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["name"] == "Test Tech Focus"
    assert data["description"] == "Narrow universe for backtesting tech-only strategies"
    assert data["asset_count"] == 0
    assert data["tickers"] == []

    # New universe should appear in the list endpoint.
    r2 = await client.get("/api/v1/universes")
    assert r2.status_code == 200
    names = {u["name"] for u in r2.json()["data"]}
    assert "Test Tech Focus" in names


@pytest.mark.asyncio
async def test_create_duplicate_name_returns_409(client):
    # Create one with a unique name.
    r1 = await client.post("/api/v1/universes", json={"name": "DupeCheck Alpha"})
    assert r1.status_code == 201
    # Try again with the same name — must conflict.
    r2 = await client.post("/api/v1/universes", json={"name": "DupeCheck Alpha"})
    assert r2.status_code == 409
    assert "already exists" in r2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_rename_universe_succeeds(client):
    create = await client.post("/api/v1/universes", json={"name": "RenameMe v1"})
    uid = create.json()["data"]["universe_id"]
    r = await client.patch(f"/api/v1/universes/{uid}", json={"name": "RenameMe v2"})
    assert r.status_code == 200
    assert r.json()["data"]["name"] == "RenameMe v2"

    # Verify via GET — write actually persisted.
    follow = await client.get(f"/api/v1/universes/{uid}")
    assert follow.json()["data"]["name"] == "RenameMe v2"


@pytest.mark.asyncio
async def test_rename_to_existing_name_returns_409(client):
    a = await client.post("/api/v1/universes", json={"name": "Clash A"})
    b = await client.post("/api/v1/universes", json={"name": "Clash B"})
    a_id = a.json()["data"]["universe_id"]
    # Try to rename A → B's name.
    r = await client.patch(f"/api/v1/universes/{a_id}", json={"name": "Clash B"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_patch_unknown_universe_returns_404(client):
    r = await client.patch(
        "/api/v1/universes/00000000-0000-0000-0000-000000000000",
        json={"name": "ghost"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_partial_update_only_touches_provided_fields(client):
    create = await client.post("/api/v1/universes", json={
        "name": "Partial Patch Demo",
        "description": "original description",
    })
    uid = create.json()["data"]["universe_id"]
    # Patch only the name; description must not be wiped.
    r = await client.patch(f"/api/v1/universes/{uid}", json={"name": "Partial Patch v2"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["name"] == "Partial Patch v2"
    assert data["description"] == "original description"


@pytest.mark.asyncio
async def test_deactivate_one_of_many_succeeds(client):
    """A universe can be deactivated as long as it's not the last active one.
    The conftest seed already creates one universe, so we add a second, then
    deactivating either one is allowed."""
    extra = await client.post("/api/v1/universes", json={"name": "Disposable"})
    extra_id = extra.json()["data"]["universe_id"]
    r = await client.delete(f"/api/v1/universes/{extra_id}")
    assert r.status_code == 200
    assert r.json()["data"]["is_active"] is False if "is_active" in r.json()["data"] else True
    # Deactivated universe no longer in the list endpoint (which filters is_active).
    listed = await client.get("/api/v1/universes")
    listed_ids = {u["universe_id"] for u in listed.json()["data"]}
    assert extra_id not in listed_ids


@pytest.mark.asyncio
async def test_cannot_deactivate_last_active_universe(client):
    """Refuse to deactivate the only universe still active — would brick
    every downstream surface that calls /universes/default.

    Self-cleaning: the conftest DB is session-scoped, so this test
    deactivates everything-except-one as part of the assertion, then
    re-activates whatever it touched. Without the restore, downstream
    tests in other files lose the seeded universe and fail."""
    listed = await client.get("/api/v1/universes")
    active_ids = [u["universe_id"] for u in listed.json()["data"]]
    # Deactivate all but the first so exactly one remains active.
    deactivated_for_cleanup = active_ids[1:]
    try:
        for uid in deactivated_for_cleanup:
            r = await client.delete(f"/api/v1/universes/{uid}")
            assert r.status_code == 200, (uid, r.text)
        # Exactly one active universe now — deactivating it must 409.
        final = await client.get("/api/v1/universes")
        remaining = [u["universe_id"] for u in final.json()["data"]]
        assert len(remaining) == 1
        blocked = await client.delete(f"/api/v1/universes/{remaining[0]}")
        assert blocked.status_code == 409
        assert "only active universe" in blocked.json()["detail"].lower()
    finally:
        # Re-activate everything we touched so the rest of the test session
        # sees the same active set it started with.
        for uid in deactivated_for_cleanup:
            await client.patch(f"/api/v1/universes/{uid}", json={"is_active": True})
