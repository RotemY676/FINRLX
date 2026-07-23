"""Phase W-2 — investor profile API + scoring contract tests.

Coverage:
* Pure scoring: bucket mapping at every band boundary; rejects invalid
  scores; rejects missing/invalid risk answers.
* GET /profile/questions — requires auth, returns step-grouped catalog.
* GET /profile/me — empty for new user; populated after submit.
* POST /profile — creates first profile, writes a revision row.
* POST /profile — second submit upserts current row + bumps version +
  appends a second revision (audit trail).
* Tenant boundary — user A cannot see user B's profile or revisions.
* Validation errors return 422 with a useful message.
"""
from __future__ import annotations

import secrets
from typing import Any

import pytest

from app.services.profile import (
    MAX_RISK_SCORE,
    MIN_RISK_SCORE,
    ProfileValidationError,
    bucket_from_score,
    score_answers,
)

# ── Helpers ──────────────────────────────────────────────────────────


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _signup(client) -> tuple[str, str]:
    from app.models.auth import EmailAllowlist
    from tests.conftest import test_session_factory

    email = f"pr-{secrets.token_hex(4)}@example.com"
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
    """Seed the catalog into the in-memory test DB if not already present."""
    import scripts.seed_profile_questions as seed_mod
    from scripts.seed_profile_questions import QUESTIONS, seed
    from tests.conftest import test_session_factory

    original = seed_mod.async_session_factory
    seed_mod.async_session_factory = test_session_factory
    try:
        result = await seed()
    finally:
        seed_mod.async_session_factory = original
    assert result["total_now"] == len(QUESTIONS)


def _valid_answers(**overrides: Any) -> dict[str, str | list[str]]:
    """Returns a full set of wizard answers that scores to 'moderate' (20)."""
    base: dict[str, str | list[str]] = {
        # Knowledge & experience
        "K_01_LEVEL": "intermediate",
        "K_02_YEARS": "3",
        "K_03_INSTRUMENTS": ["equities", "etfs"],
        "K_04_RESEARCH": "occasionally",
        # Financial
        "F_01_INVESTABLE": "50k_250k",
        "F_02_INCOME": "50k_150k",
        "F_03_NET_WORTH": "100k_500k",
        "F_04_DEPENDENCY": "slightly",
        # Risk (8 items, each score 1..4) — choose all score=3 ⇒ total 24, bucket moderate_aggressive
        # We want 'moderate' = 20, so pick mostly 2s and a few 3s.
        "R_01_VOL_COMFORT": "3",
        "R_02_LOSS_REACTION": "3",
        "R_03_TRADEOFF": "2",
        "R_04_GAMBLE_GUARANTEE": "2",
        "R_05_INHERITANCE": "3",
        "R_06_FRIEND_TIP": "2",
        "R_07_FAMILIARITY": "3",
        "R_08_DRAWDOWN_TOLERANCE": "2",
        # Objectives
        "O_01_HORIZON": "3y_5y",
        "O_02_PRIMARY_GOAL": "growth",
        "O_03_MAX_DD": "15",
        # Universe
        "U_01_REGION": "global",
        "U_02_SECTOR_WHITELIST": ["Technology"],
        "U_03_SECTOR_BLACKLIST": [],
        "U_04_LEVERAGE": "no",
        # Operational
        "P_01_CURRENCY": "USD",
        "P_02_FREQUENCY": "monthly",
        "P_03_NOTIFICATIONS": "important",
    }
    base.update(overrides)
    return base


# ── Pure scoring tests ───────────────────────────────────────────────


def test_bucket_boundaries():
    assert bucket_from_score(8) == "conservative"
    assert bucket_from_score(12) == "conservative"
    assert bucket_from_score(13) == "moderate_conservative"
    assert bucket_from_score(17) == "moderate_conservative"
    assert bucket_from_score(18) == "moderate"
    assert bucket_from_score(22) == "moderate"
    assert bucket_from_score(23) == "moderate_aggressive"
    assert bucket_from_score(27) == "moderate_aggressive"
    assert bucket_from_score(28) == "aggressive"
    assert bucket_from_score(32) == "aggressive"


def test_bucket_rejects_out_of_range():
    for bad in (MIN_RISK_SCORE - 1, MAX_RISK_SCORE + 1, 0, 100):
        with pytest.raises(ProfileValidationError):
            bucket_from_score(bad)


def _make_risk_choices() -> dict[str, list[dict]]:
    return {
        f"R_{i:02d}_X": [
            {"value": "1", "label": "A", "score": 1},
            {"value": "2", "label": "B", "score": 2},
            {"value": "3", "label": "C", "score": 3},
            {"value": "4", "label": "D", "score": 4},
        ]
        for i in range(1, 9)
    }


def test_score_answers_full_low_bucket():
    risk_choices = _make_risk_choices()
    answers = _valid_answers(
        **{code: "1" for code in risk_choices}
    )
    scored = score_answers(answers, risk_choices)
    assert scored.risk_score == 8
    assert scored.risk_bucket == "conservative"


def test_score_answers_full_high_bucket():
    risk_choices = _make_risk_choices()
    answers = _valid_answers(
        **{code: "4" for code in risk_choices}
    )
    scored = score_answers(answers, risk_choices)
    assert scored.risk_score == 32
    assert scored.risk_bucket == "aggressive"


def test_score_answers_rejects_missing_risk_item():
    risk_choices = _make_risk_choices()
    answers = _valid_answers()
    # Remove one risk answer
    del answers["R_01_VOL_COMFORT"]
    # The fixture risk codes (R_01_X..R_08_X) match scoring loop keys, so
    # use the matching set of codes from the catalog instead.
    catalog_risk_choices = {
        f"R_{i:02d}_X": risk_choices[f"R_{i:02d}_X"] for i in range(1, 9)
    }
    catalog_risk_choices["R_01_VOL_COMFORT"] = risk_choices["R_01_X"]
    with pytest.raises(ProfileValidationError, match="missing required answer"):
        score_answers(answers, catalog_risk_choices)


def test_score_answers_rejects_invalid_enum():
    risk_choices = _make_risk_choices()
    answers = _valid_answers(O_01_HORIZON="bogus")
    answers.update({code: "2" for code in risk_choices})
    with pytest.raises(ProfileValidationError, match="O_01_HORIZON"):
        score_answers(answers, risk_choices)


# ── API tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_questions_requires_auth(anon_client):
    await _ensure_questions_seeded()
    r = await anon_client.get("/api/v1/profile/questions")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_get_questions_returns_step_grouped(client):
    await _ensure_questions_seeded()
    _, token = await _signup(client)
    r = await client.get("/api/v1/profile/questions", headers=_bearer(token))
    assert r.status_code == 200
    steps = r.json()["data"]
    step_numbers = [s["step"] for s in steps]
    # Steps 2..7 must all be present after seeding.
    for expected in (2, 3, 4, 5, 6, 7):
        assert expected in step_numbers
    risk_step = next(s for s in steps if s["step"] == 4)
    assert len(risk_step["questions"]) == 8
    # Each risk choice must have a score 1..4.
    for q in risk_step["questions"]:
        scores = sorted(c["score"] for c in q["choices"])
        assert scores == [1, 2, 3, 4]


@pytest.mark.asyncio
async def test_get_me_empty_then_populated(client):
    await _ensure_questions_seeded()
    _, token = await _signup(client)

    r = await client.get("/api/v1/profile/me", headers=_bearer(token))
    assert r.status_code == 200
    body = r.json()["data"]
    assert body["has_profile"] is False
    assert body["profile"] is None

    r = await client.post(
        "/api/v1/profile",
        headers=_bearer(token),
        json={"answers": _valid_answers(), "change_summary": "first save"},
    )
    assert r.status_code == 201, r.text
    created = r.json()["data"]
    assert created["risk_bucket"] in {"moderate", "moderate_conservative", "moderate_aggressive"}
    assert created["version"] == 1
    assert created["base_currency"] == "USD"
    assert "Technology" in created["sector_whitelist"]
    assert created["exclude_leverage"] is True

    r = await client.get("/api/v1/profile/me", headers=_bearer(token))
    assert r.status_code == 200
    body = r.json()["data"]
    assert body["has_profile"] is True
    assert body["profile"]["id"] == created["id"]


@pytest.mark.asyncio
async def test_post_profile_writes_revision(client):
    await _ensure_questions_seeded()
    _, token = await _signup(client)

    await client.post(
        "/api/v1/profile",
        headers=_bearer(token),
        json={"answers": _valid_answers()},
    )
    r = await client.get("/api/v1/profile/revisions/me", headers=_bearer(token))
    assert r.status_code == 200
    revisions = r.json()["data"]
    assert len(revisions) == 1
    assert revisions[0]["version"] == 1


@pytest.mark.asyncio
async def test_second_submit_bumps_version_and_appends_revision(client):
    await _ensure_questions_seeded()
    _, token = await _signup(client)

    await client.post(
        "/api/v1/profile",
        headers=_bearer(token),
        json={"answers": _valid_answers()},
    )
    await client.post(
        "/api/v1/profile",
        headers=_bearer(token),
        json={
            "answers": _valid_answers(P_01_CURRENCY="EUR"),
            "change_summary": "switched to EUR",
        },
    )
    r = await client.get("/api/v1/profile/me", headers=_bearer(token))
    body = r.json()["data"]
    assert body["profile"]["version"] == 2
    assert body["profile"]["base_currency"] == "EUR"

    r = await client.get("/api/v1/profile/revisions/me", headers=_bearer(token))
    revisions = r.json()["data"]
    assert [rev["version"] for rev in revisions] == [2, 1]
    assert revisions[0]["change_summary"] == "switched to EUR"


@pytest.mark.asyncio
async def test_tenant_boundary_other_user_cannot_see_profile(client):
    await _ensure_questions_seeded()
    _, token_a = await _signup(client)
    _, token_b = await _signup(client)

    await client.post(
        "/api/v1/profile",
        headers=_bearer(token_a),
        json={"answers": _valid_answers()},
    )
    r = await client.get("/api/v1/profile/me", headers=_bearer(token_b))
    body = r.json()["data"]
    assert body["has_profile"] is False
    assert body["profile"] is None

    r = await client.get(
        "/api/v1/profile/revisions/me", headers=_bearer(token_b)
    )
    assert r.json()["data"] == []


@pytest.mark.asyncio
async def test_invalid_submission_returns_422(client):
    await _ensure_questions_seeded()
    _, token = await _signup(client)

    bad = _valid_answers(O_01_HORIZON="bogus")
    r = await client.post(
        "/api/v1/profile",
        headers=_bearer(token),
        json={"answers": bad},
    )
    assert r.status_code == 422
    assert "O_01_HORIZON" in r.json()["detail"]
