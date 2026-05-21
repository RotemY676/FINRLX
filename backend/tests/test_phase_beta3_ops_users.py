"""Phase BETA-3 — /api/v1/ops/users contract."""
from __future__ import annotations

import secrets

import pytest


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _signup(client, *, role: str = "user") -> tuple[str, str, str]:
    from sqlalchemy import select

    from app.models.auth import EmailAllowlist, User
    from tests.conftest import test_session_factory

    email = f"beta3-{role}-{secrets.token_hex(4)}@example.com"
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
async def test_ops_users_rejected_for_non_admin(client):
    _, _, token = await _signup(client)
    r = await client.get("/api/v1/ops/users", headers=_bearer(token))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_ops_users_admin_sees_all_users(client):
    _, _, admin_token = await _signup(client, role="admin")
    _, user_email, _ = await _signup(client)

    r = await client.get("/api/v1/ops/users", headers=_bearer(admin_token))
    assert r.status_code == 200, r.text
    rows = r.json()["data"]
    emails = [row["email"] for row in rows]
    assert user_email in emails


@pytest.mark.asyncio
async def test_ops_users_reflects_profile_completion(client):
    """A user who's completed the wizard shows has_profile=true + version."""
    import scripts.seed_profile_questions as seed_mod
    from scripts.seed_profile_questions import seed
    from tests.conftest import test_session_factory

    original = seed_mod.async_session_factory
    seed_mod.async_session_factory = test_session_factory
    try:
        await seed()
    finally:
        seed_mod.async_session_factory = original

    _, _, admin_token = await _signup(client, role="admin")
    _, user_email, user_token = await _signup(client)

    answers = {
        "K_01_LEVEL": "intermediate", "K_02_YEARS": "3",
        "K_03_INSTRUMENTS": ["equities"], "K_04_RESEARCH": "occasionally",
        "F_01_INVESTABLE": "50k_250k", "F_02_INCOME": "50k_150k",
        "F_03_NET_WORTH": "100k_500k", "F_04_DEPENDENCY": "slightly",
        "R_01_VOL_COMFORT": "2", "R_02_LOSS_REACTION": "2",
        "R_03_TRADEOFF": "2", "R_04_GAMBLE_GUARANTEE": "2",
        "R_05_INHERITANCE": "2", "R_06_FRIEND_TIP": "2",
        "R_07_FAMILIARITY": "2", "R_08_DRAWDOWN_TOLERANCE": "2",
        "O_01_HORIZON": "3y_5y", "O_02_PRIMARY_GOAL": "growth",
        "O_03_MAX_DD": "15", "U_01_REGION": "global",
        "U_02_SECTOR_WHITELIST": [], "U_03_SECTOR_BLACKLIST": [],
        "U_04_LEVERAGE": "no", "P_01_CURRENCY": "USD",
        "P_02_FREQUENCY": "monthly", "P_03_NOTIFICATIONS": "important",
    }
    await client.post(
        "/api/v1/profile", headers=_bearer(user_token),
        json={"answers": answers},
    )

    r = await client.get("/api/v1/ops/users", headers=_bearer(admin_token))
    rows = r.json()["data"]
    me = next(row for row in rows if row["email"] == user_email)
    assert me["has_profile"] is True
    assert me["profile_version"] == 1
