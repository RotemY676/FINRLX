"""Phase MVP-1 — Identity & tenant boundary tests.

Covers:
- Happy paths: signup, login, refresh rotation, me, logout
- Broken-auth attacks (OWASP A07 patterns):
    * Username enumeration via differential error
    * Account-status-leak
    * Weak-password rejection
    * Bearer-token tampering / missing alg
    * Refresh-token replay after revoke
    * Refresh-token replay after rotation (parent must die)
    * Cross-token-type misuse (refresh used as access)
- IDOR attacks (OWASP A01):
    * Tenant A can not /auth/me as tenant B (token belongs to A)
    * Tenant A can not /auth/logout tenant B's refresh token
    * Tenant A can not derive tenant B's identity from JWT (sub is opaque UUID)
- Allowlist enforcement: signup is blocked if email not in allowlist

These tests use the in-memory SQLite fixture from conftest.
"""
from __future__ import annotations

import uuid

import pytest

from app.core.auth import (
    generate_refresh_token_pair,
    hash_refresh_token,
    issue_access_token,
)
from app.models.auth import EmailAllowlist, RefreshToken
from tests.conftest import test_session_factory as AsyncSessionLocal


# ---------- helpers ---------------------------------------------------------

def _u(prefix: str) -> str:
    # Unique email per test to avoid 409s across tests in the same session.
    return f"{prefix}-{uuid.uuid4().hex[:10]}@beta.example.com"


async def _allowlist(email: str) -> None:
    async with AsyncSessionLocal() as db:
        db.add(EmailAllowlist(email=email))
        await db.commit()


async def _signup(client, email: str, password: str = "correct-horse-battery-staple"):
    await _allowlist(email)
    r = await client.post("/api/v1/auth/signup", json={"email": email, "password": password})
    return r


async def _login(client, email: str, password: str = "correct-horse-battery-staple"):
    return await client.post("/api/v1/auth/login", json={"email": email, "password": password})


def _bearer(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


# ---------- happy paths -----------------------------------------------------

@pytest.mark.asyncio
async def test_signup_returns_user_and_tokens(client):
    email = _u("happy-signup")
    r = await _signup(client, email)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["user"]["email"] == email
    assert body["user"]["role"] == "user"
    assert body["user"]["is_active"] is True
    assert body["tokens"]["token_type"] == "Bearer"
    assert len(body["tokens"]["access_token"]) > 50
    assert len(body["tokens"]["refresh_token"]) > 40


@pytest.mark.asyncio
async def test_login_after_signup_returns_new_token_pair(client):
    email = _u("happy-login")
    await _signup(client, email)
    r = await _login(client, email)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["user"]["email"] == email
    assert body["tokens"]["access_token"]
    assert body["tokens"]["refresh_token"]


@pytest.mark.asyncio
async def test_me_returns_authenticated_user(client):
    email = _u("happy-me")
    signup_res = (await _signup(client, email)).json()
    r = await client.get("/api/v1/auth/me", headers=_bearer(signup_res["tokens"]["access_token"]))
    assert r.status_code == 200, r.text
    assert r.json()["email"] == email


@pytest.mark.asyncio
async def test_refresh_rotates_tokens_and_revokes_parent(client):
    email = _u("happy-refresh")
    signup_res = (await _signup(client, email)).json()
    parent_refresh = signup_res["tokens"]["refresh_token"]

    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": parent_refresh})
    assert r.status_code == 200, r.text
    new_pair = r.json()
    assert new_pair["refresh_token"] != parent_refresh

    # Parent must now be revoked — using it again must fail.
    r2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": parent_refresh})
    assert r2.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client):
    email = _u("happy-logout")
    signup_res = (await _signup(client, email)).json()
    access = signup_res["tokens"]["access_token"]
    refresh = signup_res["tokens"]["refresh_token"]

    r = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh},
        headers=_bearer(access),
    )
    assert r.status_code == 200, r.text

    # Refresh must now fail.
    r2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r2.status_code == 401


# ---------- broken authentication attacks -----------------------------------

@pytest.mark.asyncio
async def test_signup_rejects_email_not_on_allowlist(client):
    email = f"not-allowed-{uuid.uuid4().hex[:10]}@beta.example.com"
    r = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "correct-horse-battery-staple"},
    )
    assert r.status_code == 403, r.text


@pytest.mark.asyncio
async def test_signup_rejects_weak_password(client):
    email = _u("weak-pw")
    await _allowlist(email)
    r = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "short"},
    )
    # Pydantic validation -> 422
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_login_generic_error_does_not_leak_user_existence(client):
    """Same status + message whether user exists or not (no username enumeration)."""
    email_exists = _u("enum-exists")
    await _signup(client, email_exists)
    email_missing = f"nobody-{uuid.uuid4().hex[:10]}@beta.example.com"

    r1 = await _login(client, email_exists, password="WrongPassword!")
    r2 = await _login(client, email_missing, password="WrongPassword!")
    assert r1.status_code == 401
    assert r2.status_code == 401
    assert r1.json() == r2.json()


@pytest.mark.asyncio
async def test_me_rejects_missing_bearer(client):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_rejects_tampered_jwt_signature(client):
    email = _u("tamper-sig")
    signup_res = (await _signup(client, email)).json()
    access = signup_res["tokens"]["access_token"]
    # Flip a char in the middle of the signature. Tampering only the very
    # last char is unreliable: in base64url the final char of an HMAC-SHA256
    # signature carries 2 effective bits (rest is padding), so swapping it for
    # a neighbouring char in 'A'..'P' can decode to the same bytes and the
    # signature still verifies (~25% false-pass flake before this fix).
    sig_start = access.rfind(".") + 1
    pivot = sig_start + 4
    tampered = (
        access[:pivot]
        + ("A" if access[pivot] != "A" else "B")
        + access[pivot + 1 :]
    )
    r = await client.get("/api/v1/auth/me", headers=_bearer(tampered))
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_rejects_none_algorithm_attack(client):
    """Classic alg=none JWT attack — token decoded without signature must fail."""
    fake = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJhbnktdXNlci1pZCIsInJvbGUiOiJhZG1pbiIsInR5cCI6ImFjY2VzcyIsImlhdCI6MTcwMDAwMDAwMCwiZXhwIjo5OTk5OTk5OTk5fQ."
    r = await client.get("/api/v1/auth/me", headers=_bearer(fake))
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_rejects_refresh_token_used_as_bearer(client):
    """A refresh token (opaque random string) is not a valid JWT — must 401."""
    email = _u("refresh-as-bearer")
    signup_res = (await _signup(client, email)).json()
    refresh = signup_res["tokens"]["refresh_token"]
    r = await client.get("/api/v1/auth/me", headers=_bearer(refresh))
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_refresh_rejects_unknown_plaintext(client):
    plain, _ = generate_refresh_token_pair()
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": plain})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_refresh_rejects_after_logout(client):
    email = _u("refresh-after-logout")
    signup_res = (await _signup(client, email)).json()
    access = signup_res["tokens"]["access_token"]
    refresh = signup_res["tokens"]["refresh_token"]
    await client.post("/api/v1/auth/logout", json={"refresh_token": refresh}, headers=_bearer(access))
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_signup_rejects_duplicate_email(client):
    email = _u("dup")
    r1 = await _signup(client, email)
    assert r1.status_code == 201
    r2 = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "correct-horse-battery-staple"},
    )
    assert r2.status_code == 409


# ---------- IDOR / tenant boundary ------------------------------------------

@pytest.mark.asyncio
async def test_user_a_cannot_logout_user_b_refresh_token(client):
    email_a = _u("idor-a")
    email_b = _u("idor-b")
    a = (await _signup(client, email_a)).json()
    b = (await _signup(client, email_b)).json()
    r = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": b["tokens"]["refresh_token"]},
        headers=_bearer(a["tokens"]["access_token"]),  # Authenticated as A
    )
    assert r.status_code == 403
    # B's refresh token must still work for B.
    r2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": b["tokens"]["refresh_token"]})
    assert r2.status_code == 200


@pytest.mark.asyncio
async def test_user_a_me_returns_a_not_b(client):
    email_a = _u("me-a")
    email_b = _u("me-b")
    a = (await _signup(client, email_a)).json()
    (await _signup(client, email_b)).json()
    r = await client.get("/api/v1/auth/me", headers=_bearer(a["tokens"]["access_token"]))
    assert r.status_code == 200
    assert r.json()["email"] == email_a
    assert r.json()["email"] != email_b


@pytest.mark.asyncio
async def test_forged_jwt_sub_for_another_user_is_rejected_if_signed_wrong(client):
    """Even if the attacker knows the victim's user_id, they cannot mint a token without the secret."""
    import jwt as pyjwt
    email_victim = _u("victim")
    victim = (await _signup(client, email_victim)).json()
    victim_id = victim["user"]["id"]

    forged = pyjwt.encode(
        {"sub": victim_id, "role": "user", "typ": "access", "iat": 1, "exp": 9999999999},
        "WRONG-secret",
        algorithm="HS256",
    )
    r = await client.get("/api/v1/auth/me", headers=_bearer(forged))
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_storage_is_hash_only(client):
    """Defense-in-depth: the DB must never store the plaintext refresh token."""
    from sqlalchemy import select
    email = _u("hash-only")
    signup_res = (await _signup(client, email)).json()
    plain = signup_res["tokens"]["refresh_token"]
    expected_hash = hash_refresh_token(plain)
    async with AsyncSessionLocal() as db:
        # Plaintext must never appear in token_hash column.
        bad = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == plain))
        assert bad.scalar_one_or_none() is None
        # The SHA-256 of plaintext must be present.
        ok = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == expected_hash))
        assert ok.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_access_token_includes_only_opaque_uuid_sub(client):
    """Sub claim must be the opaque user_id (UUID), never the email."""
    import jwt as pyjwt
    from app.core.config import settings as cfg
    email = _u("opaque-sub")
    signup_res = (await _signup(client, email)).json()
    access = signup_res["tokens"]["access_token"]
    payload = pyjwt.decode(access, cfg.jwt_secret, algorithms=[cfg.jwt_algorithm])
    sub = payload["sub"]
    # Must be a UUID-shaped string, not the email.
    assert "@" not in sub
    assert len(sub) == 36  # UUID format
    assert sub.count("-") == 4


@pytest.mark.asyncio
async def test_expired_access_token_is_rejected(client):
    """Token with exp in the past must 401."""
    import jwt as pyjwt
    from app.core.config import settings as cfg
    forged_expired = pyjwt.encode(
        {"sub": str(uuid.uuid4()), "role": "user", "typ": "access", "iat": 1, "exp": 2},
        cfg.jwt_secret,
        algorithm=cfg.jwt_algorithm,
    )
    r = await client.get("/api/v1/auth/me", headers=_bearer(forged_expired))
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_wrong_typ_claim_is_rejected(client):
    """Token signed correctly but with typ != 'access' must be rejected."""
    import jwt as pyjwt
    from app.core.config import settings as cfg
    bad_typ = pyjwt.encode(
        {"sub": str(uuid.uuid4()), "role": "user", "typ": "refresh", "iat": 1, "exp": 9999999999},
        cfg.jwt_secret,
        algorithm=cfg.jwt_algorithm,
    )
    r = await client.get("/api/v1/auth/me", headers=_bearer(bad_typ))
    assert r.status_code == 401


# ---------- US-P0-04: refresh-token replay kills the whole chain ------------
#
# Rotation alone is not enough. If a rotated (already revoked) token is
# presented again, it leaked — but the attacker or the victim still holds the
# live child issued by the legitimate rotation, so simply 401-ing the replayed
# request leaves a working session in the thief's hands. Replay must burn the
# whole descendant chain and force a fresh login.


@pytest.mark.asyncio
async def test_replaying_a_rotated_token_revokes_the_live_descendant(client):
    email = _u("replay-chain")
    r0 = (await _signup(client, email)).json()["tokens"]["refresh_token"]

    r1 = (await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": r0}
    )).json()["refresh_token"]
    r2_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": r1})
    assert r2_res.status_code == 200, r2_res.text
    r2 = r2_res.json()["refresh_token"]

    # Sanity: the newest token is live before the replay.
    assert r2 not in (r0, r1)

    # Attacker replays the oldest, long-rotated token.
    replayed = await client.post("/api/v1/auth/refresh", json={"refresh_token": r0})
    assert replayed.status_code == 401

    # The live descendant must now be dead too — this is the point of the story.
    after = await client.post("/api/v1/auth/refresh", json={"refresh_token": r2})
    assert after.status_code == 401, (
        "replay detection must revoke the descendant chain, not just the "
        "replayed token — otherwise the stolen session survives"
    )


@pytest.mark.asyncio
async def test_replay_does_not_touch_other_sessions_of_the_same_user(client):
    """Revocation is chain-scoped: a second device must not be logged out."""
    email = _u("replay-scope")
    await _signup(client, email)

    # Two independent sessions (separate logins => separate chains).
    chain_a = (await _login(client, email)).json()["tokens"]["refresh_token"]
    chain_b = (await _login(client, email)).json()["tokens"]["refresh_token"]

    rotated_a = (await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": chain_a}
    )).json()["refresh_token"]

    # Replay chain A's parent -> A dies.
    assert (await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": chain_a}
    )).status_code == 401
    assert (await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": rotated_a}
    )).status_code == 401

    # Chain B is a different session and must survive.
    still_alive = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": chain_b}
    )
    assert still_alive.status_code == 200, (
        "replay on one chain must not log the user out of unrelated sessions"
    )


@pytest.mark.asyncio
async def test_replay_revocation_terminates_on_a_cyclic_chain(client):
    """A corrupt/crafted cycle must not hang the endpoint."""
    from sqlalchemy import select

    email = _u("replay-cycle")
    r0 = (await _signup(client, email)).json()["tokens"]["refresh_token"]
    r1 = (await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": r0}
    )).json()["refresh_token"]

    # Point the child back at its parent, creating parent -> child -> parent.
    async with AsyncSessionLocal() as db:
        parent = (await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_refresh_token(r0)
            )
        )).scalar_one()
        child = (await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_refresh_token(r1)
            )
        )).scalar_one()
        child.replaced_by_id = parent.id
        await db.commit()

    # Must return promptly rather than looping forever.
    assert (await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": r0}
    )).status_code == 401
