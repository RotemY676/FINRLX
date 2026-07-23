"""Phase B3 — saved_views CRUD contract tests.

Verifies: signup gives a token, create round-trips, list returns only
my views (tenant boundary), patch updates fields, delete removes one,
and an unauthenticated request returns 401.
"""
from __future__ import annotations

import secrets

import pytest


def _bearer(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


async def _signup(client) -> tuple[str, str]:
    """Returns (user_id, access_token) after creating a fresh allowlisted account."""
    from app.models.auth import EmailAllowlist
    from tests.conftest import test_session_factory

    # Unique email per test so the allowlist + users table stay clean.
    email = f"sv-{secrets.token_hex(4)}@example.com"
    async with test_session_factory() as db:
        db.add(EmailAllowlist(email=email))
        await db.commit()

    r = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "a-strong-password-12345"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    return body["user"]["id"], body["tokens"]["access_token"]


@pytest.mark.asyncio
async def test_create_list_round_trip(client):
    _, token = await _signup(client)

    r = await client.post(
        "/api/v1/saved-views",
        headers=_bearer(token),
        json={
            "name": "My breach watch",
            "scope": "ops",
            "filters": {"severity": "high"},
            "tone": "text-breach",
        },
    )
    assert r.status_code == 200, r.text
    created = r.json()["data"]
    assert created["name"] == "My breach watch"
    assert created["scope"] == "ops"
    assert created["filters"] == {"severity": "high"}
    assert created["tone"] == "text-breach"
    assert created["id"]
    assert created["created_at"]

    r = await client.get("/api/v1/saved-views", headers=_bearer(token))
    assert r.status_code == 200
    items = r.json()["data"]
    assert len(items) == 1
    assert items[0]["id"] == created["id"]


@pytest.mark.asyncio
async def test_list_is_scoped_to_caller_only(client):
    _, token_a = await _signup(client)
    _, token_b = await _signup(client)

    await client.post(
        "/api/v1/saved-views",
        headers=_bearer(token_a),
        json={"name": "A1", "scope": "ops", "filters": {}},
    )
    await client.post(
        "/api/v1/saved-views",
        headers=_bearer(token_b),
        json={"name": "B1", "scope": "ops", "filters": {}},
    )

    a_list = (await client.get("/api/v1/saved-views", headers=_bearer(token_a))).json()["data"]
    b_list = (await client.get("/api/v1/saved-views", headers=_bearer(token_b))).json()["data"]
    a_names = {v["name"] for v in a_list}
    b_names = {v["name"] for v in b_list}
    assert "A1" in a_names and "B1" not in a_names
    assert "B1" in b_names and "A1" not in b_names


@pytest.mark.asyncio
async def test_patch_updates_fields(client):
    _, token = await _signup(client)
    created = (await client.post(
        "/api/v1/saved-views",
        headers=_bearer(token),
        json={"name": "old name", "scope": "ops", "filters": {"k": 1}},
    )).json()["data"]

    r = await client.patch(
        f"/api/v1/saved-views/{created['id']}",
        headers=_bearer(token),
        json={"name": "new name", "filters": {"k": 2, "extra": "yes"}},
    )
    assert r.status_code == 200, r.text
    updated = r.json()["data"]
    assert updated["name"] == "new name"
    assert updated["scope"] == "ops"  # unchanged
    assert updated["filters"] == {"k": 2, "extra": "yes"}


@pytest.mark.asyncio
async def test_delete_removes_and_404s_thereafter(client):
    _, token = await _signup(client)
    created = (await client.post(
        "/api/v1/saved-views",
        headers=_bearer(token),
        json={"name": "to delete", "scope": "ops", "filters": {}},
    )).json()["data"]

    r = await client.delete(f"/api/v1/saved-views/{created['id']}", headers=_bearer(token))
    assert r.status_code == 200
    assert r.json()["data"]["deleted"] is True

    r = await client.patch(
        f"/api/v1/saved-views/{created['id']}",
        headers=_bearer(token),
        json={"name": "ghost"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_patch_another_users_view_returns_404_not_403(client):
    _, token_a = await _signup(client)
    _, token_b = await _signup(client)
    created = (await client.post(
        "/api/v1/saved-views",
        headers=_bearer(token_a),
        json={"name": "A's view", "scope": "ops", "filters": {}},
    )).json()["data"]

    r = await client.patch(
        f"/api/v1/saved-views/{created['id']}",
        headers=_bearer(token_b),
        json={"name": "hijack"},
    )
    # 404 (not 403) so we don't leak "exists but you can't see it"
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(anon_client):
    r = await anon_client.get("/api/v1/saved-views")
    assert r.status_code in (401, 403)
