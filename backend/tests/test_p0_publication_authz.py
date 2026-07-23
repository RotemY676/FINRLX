"""US-P0-03 enforcement — publication governance mutations require auth.

The stage/approve/publish/defer/suppress transitions change what is published to
users, so they must never be callable anonymously. These tests use a REAL bearer
token (not a dependency override) to prove the gate end-to-end.
"""
from __future__ import annotations

import uuid

import pytest

from app.core.auth import hash_password, issue_access_token
from app.models.auth import User
from tests.conftest import test_session_factory as AsyncSessionLocal

MUTATIONS = ["stage", "approve", "publish", "defer", "suppress"]


def _uid() -> str:
    return str(uuid.uuid4())


async def _token() -> dict[str, str]:
    uid = _uid()
    async with AsyncSessionLocal() as db:
        db.add(User(id=uid, email=f"pub-{uid[:8]}@example.com",
                    password_hash=hash_password("x"), is_active=True, role="user"))
        await db.commit()
    tok, _ = issue_access_token(user_id=uid, role="user")
    return {"Authorization": f"Bearer {tok}"}


@pytest.mark.asyncio
@pytest.mark.parametrize("action", MUTATIONS)
async def test_publication_mutation_rejects_anonymous(anon_client, action):
    r = await anon_client.post(
        f"/api/v1/publication/recommendations/{_uid()}/{action}",
        json={"actor": "anon", "reason": "x"},
    )
    assert r.status_code == 401, f"{action} must require auth, got {r.status_code}: {r.text}"


@pytest.mark.asyncio
@pytest.mark.parametrize("action", MUTATIONS)
async def test_publication_mutation_passes_auth_with_token(client, action):
    headers = await _token()
    r = await client.post(
        f"/api/v1/publication/recommendations/{_uid()}/{action}",
        json={"actor": "operator", "reason": "x"},
        headers=headers,
    )
    # A real token must clear the auth gate — never 401/403. (The transition
    # itself may be allowed/blocked on its merits; that is not an auth failure.)
    assert r.status_code not in (401, 403), f"{action} auth failed with token: {r.text}"


@pytest.mark.asyncio
async def test_publication_reads_remain_public(client):
    # GET gates/history/status/queue are not part of this enforcement slice.
    r = await client.get(f"/api/v1/publication/recommendations/{_uid()}/gates")
    assert r.status_code != 401
