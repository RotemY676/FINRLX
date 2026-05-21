"""Phase TPL-4 — admin CRUD for user-authored templates.

Coverage:
* POST /templates rejected for non-admin (403)
* POST /templates rejected if key collides (409)
* POST /templates rejected if (bucket, horizon) invalid (422)
* POST /templates succeeds for admin with valid payload (201)
* PUT  /templates/{key} rejected for non-admin (403)
* PUT  /templates/{key} rejected on a seed template (403 immutable)
* PUT  /templates/{key} 404 for unknown key
* PUT  /templates/{key} partial update preserves unset fields
* PUT  /templates/{key} recomputes allocation_summary on bucket/horizon change
* DEL  /templates/{key} rejected for non-admin (403)
* DEL  /templates/{key} rejected for seed templates (403)
* DEL  /templates/{key} removes a user-authored template
"""
from __future__ import annotations

import secrets

import pytest

from app.models.auth import EmailAllowlist


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _signup(client, *, role: str = "user") -> tuple[str, str]:
    from sqlalchemy import select

    from app.models.auth import User
    from tests.conftest import test_session_factory

    email = f"tpl4-{role}-{secrets.token_hex(4)}@example.com"
    async with test_session_factory() as db:
        db.add(EmailAllowlist(email=email))
        await db.commit()
    r = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "a-strong-password-12345"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    user_id = body["user"]["id"]
    access = body["tokens"]["access_token"]

    if role != "user":
        # Promote the freshly-created user to the requested role.
        async with test_session_factory() as db:
            u = (
                await db.execute(select(User).where(User.id == user_id))
            ).scalar_one()
            u.role = role
            await db.commit()
        # Re-login so the JWT carries the new role.
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "a-strong-password-12345"},
        )
        assert r.status_code == 200, r.text
        access = r.json()["tokens"]["access_token"]

    return user_id, access


async def _ensure_templates_seeded() -> None:
    import scripts.seed_recommendation_templates as seed_mod
    from scripts.seed_recommendation_templates import seed
    from tests.conftest import test_session_factory

    original = seed_mod.async_session_factory
    seed_mod.async_session_factory = test_session_factory
    try:
        await seed()
    finally:
        seed_mod.async_session_factory = original


def _valid_create_payload(key: str) -> dict:
    return {
        "key": key,
        "name": "My Custom Template",
        "description": "Test template authored via admin CRUD",
        "badge": "Moderate",
        "risk_bucket": "moderate",
        "horizon_band": "3y_5y",
        "primary_goal": "growth",
        "max_drawdown_pct": 15.0,
        "sector_whitelist": ["Healthcare"],
        "sector_blacklist": [],
        "exclude_leverage": True,
        "base_currency": "USD",
        "trading_frequency": "monthly",
        "region_preference": "global",
    }


# ── POST /templates ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_rejected_for_non_admin(client):
    _, token = await _signup(client, role="user")
    r = await client.post(
        "/api/v1/templates",
        headers=_bearer(token),
        json=_valid_create_payload(f"k-{secrets.token_hex(4)}"),
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_create_succeeds_for_admin(client):
    _, admin_token = await _signup(client, role="admin")
    key = f"my-template-{secrets.token_hex(4)}"
    r = await client.post(
        "/api/v1/templates",
        headers=_bearer(admin_token),
        json=_valid_create_payload(key),
    )
    assert r.status_code == 201, r.text
    body = r.json()["data"]
    assert body["key"] == key
    assert body["is_seed"] is False
    assert body["allocation_summary"] == "55/45"  # moderate + 3y_5y
    assert "Healthcare" in body["sector_whitelist"]


@pytest.mark.asyncio
async def test_create_key_collision_returns_409(client):
    await _ensure_templates_seeded()
    _, admin_token = await _signup(client, role="admin")
    payload = _valid_create_payload("balanced_growth")  # already seeded
    r = await client.post(
        "/api/v1/templates", headers=_bearer(admin_token), json=payload
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_create_invalid_bucket_horizon_returns_422(client):
    _, admin_token = await _signup(client, role="admin")
    payload = _valid_create_payload(f"bad-{secrets.token_hex(4)}")
    payload["risk_bucket"] = "ultra_aggressive"
    r = await client.post(
        "/api/v1/templates", headers=_bearer(admin_token), json=payload
    )
    assert r.status_code == 422


# ── PUT /templates/{key} ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_rejected_for_non_admin(client):
    await _ensure_templates_seeded()
    _, admin_token = await _signup(client, role="admin")
    _, user_token = await _signup(client, role="user")
    # Create a user-authored template as admin first
    key = f"upd-{secrets.token_hex(4)}"
    await client.post(
        "/api/v1/templates",
        headers=_bearer(admin_token),
        json=_valid_create_payload(key),
    )
    r = await client.put(
        f"/api/v1/templates/{key}",
        headers=_bearer(user_token),
        json={"name": "Hacker tried"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_update_rejected_for_seed_template(client):
    await _ensure_templates_seeded()
    _, admin_token = await _signup(client, role="admin")
    r = await client.put(
        "/api/v1/templates/balanced_growth",
        headers=_bearer(admin_token),
        json={"name": "Tampered"},
    )
    assert r.status_code == 403
    assert "immutable" in r.json()["detail"]


@pytest.mark.asyncio
async def test_update_404_unknown_key(client):
    _, admin_token = await _signup(client, role="admin")
    r = await client.put(
        "/api/v1/templates/does_not_exist",
        headers=_bearer(admin_token),
        json={"name": "Whatever"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_partial_preserves_unset_fields(client):
    _, admin_token = await _signup(client, role="admin")
    key = f"part-{secrets.token_hex(4)}"
    await client.post(
        "/api/v1/templates",
        headers=_bearer(admin_token),
        json=_valid_create_payload(key),
    )
    r = await client.put(
        f"/api/v1/templates/{key}",
        headers=_bearer(admin_token),
        json={"name": "Renamed only"},
    )
    assert r.status_code == 200, r.text
    body = r.json()["data"]
    assert body["name"] == "Renamed only"
    assert body["risk_bucket"] == "moderate"  # untouched
    assert "Healthcare" in body["sector_whitelist"]


@pytest.mark.asyncio
async def test_update_recomputes_allocation_summary(client):
    _, admin_token = await _signup(client, role="admin")
    key = f"alloc-{secrets.token_hex(4)}"
    await client.post(
        "/api/v1/templates",
        headers=_bearer(admin_token),
        json=_valid_create_payload(key),
    )
    r = await client.put(
        f"/api/v1/templates/{key}",
        headers=_bearer(admin_token),
        json={"risk_bucket": "aggressive", "horizon_band": "gt_10y"},
    )
    assert r.status_code == 200, r.text
    body = r.json()["data"]
    assert body["risk_bucket"] == "aggressive"
    assert body["allocation_summary"] == "95/5"  # aggressive + gt_10y


# ── DELETE /templates/{key} ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_rejected_for_non_admin(client):
    await _ensure_templates_seeded()
    _, admin_token = await _signup(client, role="admin")
    _, user_token = await _signup(client, role="user")
    key = f"del-{secrets.token_hex(4)}"
    await client.post(
        "/api/v1/templates",
        headers=_bearer(admin_token),
        json=_valid_create_payload(key),
    )
    r = await client.delete(
        f"/api/v1/templates/{key}", headers=_bearer(user_token)
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_delete_rejected_for_seed_template(client):
    await _ensure_templates_seeded()
    _, admin_token = await _signup(client, role="admin")
    r = await client.delete(
        "/api/v1/templates/balanced_growth",
        headers=_bearer(admin_token),
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_delete_removes_user_authored_template(client):
    _, admin_token = await _signup(client, role="admin")
    key = f"rm-{secrets.token_hex(4)}"
    await client.post(
        "/api/v1/templates",
        headers=_bearer(admin_token),
        json=_valid_create_payload(key),
    )
    r = await client.delete(
        f"/api/v1/templates/{key}", headers=_bearer(admin_token)
    )
    assert r.status_code == 200
    assert r.json()["data"]["deleted"] is True

    r = await client.get(
        f"/api/v1/templates/{key}", headers=_bearer(admin_token)
    )
    assert r.status_code == 404
