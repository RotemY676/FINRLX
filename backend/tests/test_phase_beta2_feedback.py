"""Phase BETA-2 — feedback API contract."""
from __future__ import annotations

import secrets

import pytest


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _signup(client, *, role: str = "user") -> tuple[str, str, str]:
    from sqlalchemy import select

    from app.models.auth import EmailAllowlist, User
    from tests.conftest import test_session_factory

    email = f"beta2-{role}-{secrets.token_hex(4)}@example.com"
    async with test_session_factory() as db:
        db.add(EmailAllowlist(email=email))
        await db.commit()
    r = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "a-strong-password-12345"},
    )
    body = r.json()
    user_id = body["user"]["id"]
    access = body["tokens"]["access_token"]
    if role != "user":
        async with test_session_factory() as db:
            u = (
                await db.execute(select(User).where(User.id == user_id))
            ).scalar_one()
            u.role = role
            await db.commit()
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "a-strong-password-12345"},
        )
        access = r.json()["tokens"]["access_token"]
    return user_id, email, access


@pytest.mark.asyncio
async def test_submit_feedback_requires_auth(client):
    r = await client.post(
        "/api/v1/feedback", json={"message": "anonymous attempt"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_submit_feedback_persists_with_user_email(client):
    _, email, token = await _signup(client)
    r = await client.post(
        "/api/v1/feedback",
        headers=_bearer(token),
        json={
            "message": "Wizard step 4 was confusing.",
            "surface": "/onboarding",
            "category": "ux",
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()["data"]
    assert body["message"] == "Wizard step 4 was confusing."
    assert body["surface"] == "/onboarding"
    assert body["category"] == "ux"
    assert body["status"] == "open"
    assert body["user_email"] == email


@pytest.mark.asyncio
async def test_list_my_feedback_returns_only_caller(client):
    _, _, token_a = await _signup(client)
    _, _, token_b = await _signup(client)
    await client.post(
        "/api/v1/feedback", headers=_bearer(token_a),
        json={"message": "A's note"},
    )
    await client.post(
        "/api/v1/feedback", headers=_bearer(token_b),
        json={"message": "B's note"},
    )
    r = await client.get("/api/v1/feedback/me", headers=_bearer(token_a))
    rows = r.json()["data"]
    assert all(row["message"] == "A's note" for row in rows)


@pytest.mark.asyncio
async def test_list_all_feedback_admin_only(client):
    _, _, user_token = await _signup(client)
    _, _, admin_token = await _signup(client, role="admin")
    await client.post(
        "/api/v1/feedback", headers=_bearer(user_token),
        json={"message": "list-all test"},
    )
    r = await client.get("/api/v1/feedback", headers=_bearer(user_token))
    assert r.status_code == 403

    r = await client.get("/api/v1/feedback", headers=_bearer(admin_token))
    assert r.status_code == 200
    body = r.json()["data"]
    assert any(row["message"] == "list-all test" for row in body)


@pytest.mark.asyncio
async def test_submit_feedback_rejects_empty(client):
    _, _, token = await _signup(client)
    r = await client.post(
        "/api/v1/feedback",
        headers=_bearer(token),
        json={"message": ""},
    )
    assert r.status_code == 422  # min_length=1 violated
