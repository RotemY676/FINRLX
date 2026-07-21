"""US-P0-01 — runtime inventory manifest (admin-only, no secret leakage)."""
from __future__ import annotations

import uuid

import pytest

from app.core.auth import hash_password, issue_access_token
from app.models.auth import User
from tests.conftest import test_session_factory as AsyncSessionLocal

INVENTORY_PATH = "/api/v1/ops/runtime-inventory"


def _uid() -> str:
    return str(uuid.uuid4())


async def _make_user(role: str) -> dict[str, str]:
    user_id = _uid()
    async with AsyncSessionLocal() as db:
        db.add(User(id=user_id, email=f"inv-{user_id[:8]}@example.com",
                    password_hash=hash_password("x"), is_active=True, role=role))
        await db.commit()
    token, _ = issue_access_token(user_id=user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_requires_authentication(client):
    r = await client.get(INVENTORY_PATH)
    assert r.status_code == 401, r.text


@pytest.mark.asyncio
async def test_non_admin_is_forbidden(client):
    headers = await _make_user("user")
    r = await client.get(INVENTORY_PATH, headers=headers)
    assert r.status_code == 403, r.text


@pytest.mark.asyncio
async def test_admin_gets_manifest_with_expected_shape(client):
    headers = await _make_user("admin")
    r = await client.get(INVENTORY_PATH, headers=headers)
    assert r.status_code == 200, r.text
    data = r.json()["data"]

    # Core sections present.
    assert data["route_count"] >= 1
    assert data["route_count"] == len(data["routes"])
    assert set(data["auth_summary"].keys()) == {"public", "optional", "required"}
    assert sum(data["auth_summary"].values()) == data["route_count"]

    # Pins are informative and honest (no fabricated commit).
    assert data["pins"]["python_version"].startswith("3.11")
    assert data["pins"]["pipeline_version"]
    assert "git_commit" in data["pins"]  # None locally, set on Railway

    # The DecisionPacket work from the prior slice is visible in the manifest.
    paths = {ri["path"] for ri in data["routes"]}
    assert any(p.endswith("/decision-packets") for p in paths)
    assert INVENTORY_PATH in paths
    flag_names = {f["name"] for f in data["flags"]}
    assert "feature_decision_packet_v1" in flag_names


@pytest.mark.asyncio
async def test_route_auth_classification_is_accurate(client):
    headers = await _make_user("admin")
    data = (await client.get(INVENTORY_PATH, headers=headers)).json()["data"]
    by_path = {ri["path"]: ri for ri in data["routes"]}

    # The inventory route itself is auth-required (admin gate lives in the body,
    # but get_current_user is a real dependency the classifier can see).
    assert by_path[INVENTORY_PATH]["auth"] == "required"
    # The decision-packets route uses get_optional_user → "optional".
    dp = next(ri for p, ri in by_path.items() if p.endswith("/decision-packets"))
    assert dp["auth"] == "optional"
    # The public flags endpoint is unauthenticated.
    assert by_path["/api/v1/flags"]["auth"] == "public"


@pytest.mark.asyncio
async def test_manifest_never_leaks_secrets(client):
    headers = await _make_user("admin")
    raw = (await client.get(INVENTORY_PATH, headers=headers)).text.lower()
    # No secret material or credential-bearing URL may appear anywhere.
    for needle in ["jwt_secret", "dev-only-not-for-production", "password", "api_key", "sqlite+aiosqlite", "database_url"]:
        assert needle not in raw, f"manifest leaked '{needle}'"
    # Provider config is boolean-only.
    data = (await client.get(INVENTORY_PATH, headers=headers)).json()["data"]
    for p in data["providers"]:
        assert isinstance(p["configured"], bool)
