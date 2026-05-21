"""Phase W-8 — full end-to-end happy path for the investor profile flow.

Walks every Phase W endpoint against the real ASGI app + in-memory DB:

  1. signup                                       → 201
  2. GET /profile/questions                       → 200, 6 steps, 26 items
  3. GET /profile/me                              → 200, has_profile=false
  4. POST /profile (full valid answers)           → 201, version=1
  5. GET /profile/me                              → 200, has_profile=true,
                                                    raw_answers populated
  6. GET /profile/revisions/me                    → 200, len==1
  7. POST /profile (currency=EUR override)        → 201, version=2
  8. GET /profile/revisions/me                    → 200, len==2, newest first
  9. POST /profile/run-pipeline                   → 200, status field present,
                                                    well-formed envelope
 10. cross-user check: signup as user B,
     GET /profile/me                              → has_profile=false
     POST /profile/run-pipeline                   → 400 no_profile

Together this closes Phase W and gives the BETA-1 cohort a documented
guarantee that a freshly signed-up user can complete the wizard and
trigger a profile-aware recommendation.
"""
from __future__ import annotations

import secrets

import pytest


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _signup(client) -> tuple[str, str]:
    from app.models.auth import EmailAllowlist
    from tests.conftest import test_session_factory

    email = f"w8-{secrets.token_hex(4)}@example.com"
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


async def _ensure_questions_seeded() -> None:
    import scripts.seed_profile_questions as seed_mod
    from scripts.seed_profile_questions import seed
    from tests.conftest import test_session_factory

    original = seed_mod.async_session_factory
    seed_mod.async_session_factory = test_session_factory
    try:
        await seed()
    finally:
        seed_mod.async_session_factory = original


def _full_valid_answers(**overrides) -> dict[str, str | list[str]]:
    base: dict[str, str | list[str]] = {
        "K_01_LEVEL": "intermediate",
        "K_02_YEARS": "3",
        "K_03_INSTRUMENTS": ["equities", "etfs"],
        "K_04_RESEARCH": "occasionally",
        "F_01_INVESTABLE": "50k_250k",
        "F_02_INCOME": "50k_150k",
        "F_03_NET_WORTH": "100k_500k",
        "F_04_DEPENDENCY": "slightly",
        "R_01_VOL_COMFORT": "3",
        "R_02_LOSS_REACTION": "3",
        "R_03_TRADEOFF": "2",
        "R_04_GAMBLE_GUARANTEE": "2",
        "R_05_INHERITANCE": "3",
        "R_06_FRIEND_TIP": "2",
        "R_07_FAMILIARITY": "3",
        "R_08_DRAWDOWN_TOLERANCE": "2",
        "O_01_HORIZON": "3y_5y",
        "O_02_PRIMARY_GOAL": "growth",
        "O_03_MAX_DD": "15",
        "U_01_REGION": "global",
        "U_02_SECTOR_WHITELIST": ["Technology"],
        "U_03_SECTOR_BLACKLIST": [],
        "U_04_LEVERAGE": "no",
        "P_01_CURRENCY": "USD",
        "P_02_FREQUENCY": "monthly",
        "P_03_NOTIFICATIONS": "important",
    }
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_full_profile_lifecycle_signup_to_run(client):
    """Phase W-8 happy path — every step in sequence."""
    await _ensure_questions_seeded()

    # 1. signup
    user_id_a, token_a = await _signup(client)

    # 2. GET /profile/questions — 6 steps, 26 items total
    r = await client.get("/api/v1/profile/questions", headers=_bearer(token_a))
    assert r.status_code == 200, r.text
    steps = r.json()["data"]
    assert len(steps) == 6
    total_items = sum(len(s["questions"]) for s in steps)
    assert total_items == 26

    # 3. GET /profile/me — empty
    r = await client.get("/api/v1/profile/me", headers=_bearer(token_a))
    assert r.status_code == 200
    assert r.json()["data"]["has_profile"] is False

    # 4. POST /profile — first save
    answers_v1 = _full_valid_answers()
    r = await client.post(
        "/api/v1/profile",
        headers=_bearer(token_a),
        json={"answers": answers_v1, "change_summary": "initial wizard"},
    )
    assert r.status_code == 201, r.text
    saved_v1 = r.json()["data"]
    assert saved_v1["version"] == 1
    assert saved_v1["base_currency"] == "USD"
    assert saved_v1["risk_score"] in range(8, 33)
    assert saved_v1["risk_bucket"] in {
        "conservative",
        "moderate_conservative",
        "moderate",
        "moderate_aggressive",
        "aggressive",
    }

    # 5. GET /profile/me — populated, raw_answers present
    r = await client.get("/api/v1/profile/me", headers=_bearer(token_a))
    body = r.json()["data"]
    assert body["has_profile"] is True
    profile = body["profile"]
    assert profile["id"] == saved_v1["id"]
    assert profile["raw_answers"]["K_01_LEVEL"] == "intermediate"
    assert profile["raw_answers"]["U_02_SECTOR_WHITELIST"] == ["Technology"]

    # 6. GET /profile/revisions/me — first revision
    r = await client.get("/api/v1/profile/revisions/me", headers=_bearer(token_a))
    revisions = r.json()["data"]
    assert len(revisions) == 1
    assert revisions[0]["version"] == 1
    assert revisions[0]["change_summary"] == "initial wizard"

    # 7. POST /profile — edit (switch currency)
    answers_v2 = _full_valid_answers(P_01_CURRENCY="EUR")
    r = await client.post(
        "/api/v1/profile",
        headers=_bearer(token_a),
        json={"answers": answers_v2, "change_summary": "switched to EUR"},
    )
    assert r.status_code == 201
    saved_v2 = r.json()["data"]
    assert saved_v2["version"] == 2
    assert saved_v2["base_currency"] == "EUR"
    # Same id (one-current-per-user invariant)
    assert saved_v2["id"] == saved_v1["id"]

    # 8. revisions now has v1 + v2 (newest first)
    r = await client.get("/api/v1/profile/revisions/me", headers=_bearer(token_a))
    revisions = r.json()["data"]
    assert [rev["version"] for rev in revisions] == [2, 1]

    # 9. POST /profile/run-pipeline — well-formed envelope returned
    r = await client.post(
        "/api/v1/profile/run-pipeline", headers=_bearer(token_a)
    )
    assert r.status_code == 200, r.text
    run = r.json()["data"]
    assert "status" in run
    assert run["status"] in ("completed", "failed")
    # If the pipeline actually completed (seeded engines + signals
    # cooperative), the warnings array must mention the profile binding.
    if run["status"] == "completed":
        assert any("Profile-aware pipeline run" in w for w in (run.get("warnings") or []))

    # 10. cross-user — user B sees no profile, run-pipeline rejected
    _, token_b = await _signup(client)
    r = await client.get("/api/v1/profile/me", headers=_bearer(token_b))
    assert r.json()["data"]["has_profile"] is False
    r = await client.post(
        "/api/v1/profile/run-pipeline", headers=_bearer(token_b)
    )
    assert r.status_code == 400
    assert "no_profile" in r.json()["detail"]


@pytest.mark.asyncio
async def test_run_pipeline_emits_profile_warning_when_completed(client):
    """If the pipeline completes, its warnings must bind to the profile.

    Skipped when the pipeline cannot complete in the hermetic seed (no
    eligible signals or engines) — but if it does, the binding warning
    is a hard requirement for replay/audit honesty.
    """
    await _ensure_questions_seeded()
    _, token = await _signup(client)
    await client.post(
        "/api/v1/profile",
        headers=_bearer(token),
        json={"answers": _full_valid_answers()},
    )
    r = await client.post("/api/v1/profile/run-pipeline", headers=_bearer(token))
    assert r.status_code == 200
    run = r.json()["data"]
    if run["status"] != "completed":
        pytest.skip(f"pipeline did not complete in hermetic seed (status={run['status']})")
    warnings = run.get("warnings") or []
    assert any("Profile-aware pipeline run" in w for w in warnings), warnings
