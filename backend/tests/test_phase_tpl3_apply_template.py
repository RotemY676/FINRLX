"""Phase TPL-3 — Apply Template to profile contract.

Coverage:
* POST /profile/apply-template/{key} rejects unknown keys with 404.
* POST /profile/apply-template/{key} requires an existing profile (400).
* POST /profile/apply-template/{key} successfully overrides
  universe + operational fields and bumps version.
* Personal dimensions (risk_score, knowledge, financial bands,
  instruments_traded) are PRESERVED.
* A new revision row is appended with change_summary "applied template:<key>".
* Cross-user check: user B's apply does not touch user A's profile.
"""
from __future__ import annotations

import secrets

import pytest


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _signup(client) -> tuple[str, str]:
    from app.models.auth import EmailAllowlist
    from tests.conftest import test_session_factory

    email = f"tpl3-{secrets.token_hex(4)}@example.com"
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


async def _ensure_seeded() -> None:
    """Seed questions + templates into the test DB."""
    import scripts.seed_profile_questions as q_seed_mod
    import scripts.seed_recommendation_templates as t_seed_mod
    from scripts.seed_profile_questions import seed as q_seed
    from scripts.seed_recommendation_templates import seed as t_seed
    from tests.conftest import test_session_factory

    for mod in (q_seed_mod, t_seed_mod):
        original = mod.async_session_factory
        mod.async_session_factory = test_session_factory
        try:
            if mod is q_seed_mod:
                await q_seed()
            else:
                await t_seed()
        finally:
            mod.async_session_factory = original


def _valid_answers(currency: str = "USD") -> dict[str, str | list[str]]:
    return {
        "K_01_LEVEL": "intermediate",
        "K_02_YEARS": "3",
        "K_03_INSTRUMENTS": ["equities"],
        "K_04_RESEARCH": "occasionally",
        "F_01_INVESTABLE": "50k_250k",
        "F_02_INCOME": "50k_150k",
        "F_03_NET_WORTH": "100k_500k",
        "F_04_DEPENDENCY": "slightly",
        "R_01_VOL_COMFORT": "2",
        "R_02_LOSS_REACTION": "2",
        "R_03_TRADEOFF": "2",
        "R_04_GAMBLE_GUARANTEE": "2",
        "R_05_INHERITANCE": "2",
        "R_06_FRIEND_TIP": "2",
        "R_07_FAMILIARITY": "2",
        "R_08_DRAWDOWN_TOLERANCE": "2",
        "O_01_HORIZON": "3y_5y",
        "O_02_PRIMARY_GOAL": "growth",
        "O_03_MAX_DD": "15",
        "U_01_REGION": "global",
        "U_02_SECTOR_WHITELIST": ["Healthcare"],
        "U_03_SECTOR_BLACKLIST": [],
        "U_04_LEVERAGE": "no",
        "P_01_CURRENCY": currency,
        "P_02_FREQUENCY": "monthly",
        "P_03_NOTIFICATIONS": "important",
    }


@pytest.mark.asyncio
async def test_apply_unknown_template_returns_404(client):
    await _ensure_seeded()
    _, token = await _signup(client)
    await client.post(
        "/api/v1/profile",
        headers=_bearer(token),
        json={"answers": _valid_answers()},
    )
    r = await client.post(
        "/api/v1/profile/apply-template/does_not_exist",
        headers=_bearer(token),
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_apply_requires_existing_profile(client):
    await _ensure_seeded()
    _, token = await _signup(client)
    r = await client.post(
        "/api/v1/profile/apply-template/balanced_growth",
        headers=_bearer(token),
    )
    assert r.status_code == 400
    assert "no_profile" in r.json()["detail"]


@pytest.mark.asyncio
async def test_apply_overrides_universe_and_preserves_personal(client):
    await _ensure_seeded()
    _, token = await _signup(client)
    await client.post(
        "/api/v1/profile",
        headers=_bearer(token),
        json={"answers": _valid_answers(currency="EUR")},
    )
    me_before = (
        await client.get("/api/v1/profile/me", headers=_bearer(token))
    ).json()["data"]["profile"]
    assert me_before["version"] == 1
    assert me_before["base_currency"] == "EUR"
    risk_score_before = me_before["risk_score"]
    investable_before = me_before["investable_amount_band"]

    r = await client.post(
        "/api/v1/profile/apply-template/tech_growth", headers=_bearer(token)
    )
    assert r.status_code == 200, r.text
    updated = r.json()["data"]
    assert updated["version"] == 2

    # Template-applied fields
    assert updated["risk_bucket"] == "aggressive"
    assert updated["horizon_band"] == "5y_10y"
    assert updated["base_currency"] == "USD"  # tech_growth seed is USD
    assert updated["trading_frequency"] == "weekly"
    assert "Technology" in updated["sector_whitelist"]

    # Personal dimensions preserved
    assert updated["risk_score"] == risk_score_before
    assert updated["investable_amount_band"] == investable_before
    assert updated["knowledge_level"] == "intermediate"


@pytest.mark.asyncio
async def test_apply_appends_revision_row(client):
    await _ensure_seeded()
    _, token = await _signup(client)
    await client.post(
        "/api/v1/profile",
        headers=_bearer(token),
        json={"answers": _valid_answers()},
    )
    await client.post(
        "/api/v1/profile/apply-template/balanced_growth",
        headers=_bearer(token),
    )
    revisions = (
        await client.get("/api/v1/profile/revisions/me", headers=_bearer(token))
    ).json()["data"]
    assert len(revisions) >= 2
    # Newest first
    assert revisions[0]["version"] == 2
    assert "applied template:balanced_growth" in (revisions[0]["change_summary"] or "")


@pytest.mark.asyncio
async def test_apply_is_per_user(client):
    await _ensure_seeded()
    _, token_a = await _signup(client)
    _, token_b = await _signup(client)
    await client.post(
        "/api/v1/profile",
        headers=_bearer(token_a),
        json={"answers": _valid_answers()},
    )
    await client.post(
        "/api/v1/profile",
        headers=_bearer(token_b),
        json={"answers": _valid_answers()},
    )

    await client.post(
        "/api/v1/profile/apply-template/tech_growth", headers=_bearer(token_a)
    )

    me_a = (
        await client.get("/api/v1/profile/me", headers=_bearer(token_a))
    ).json()["data"]["profile"]
    me_b = (
        await client.get("/api/v1/profile/me", headers=_bearer(token_b))
    ).json()["data"]["profile"]

    assert me_a["risk_bucket"] == "aggressive"
    # B is untouched
    assert me_b["risk_bucket"] != "aggressive"
    assert me_b["version"] == 1
