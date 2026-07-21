"""US-DPK-03 / US-DPK-05 — DecisionPacket read-only API (flag + auth).

Covers the feature-flag gate (off → 404, on → 200), the bundle shape with an
explicit per-packet outcome, honest fail-closed state for the (synthetic) seed
data, and cross-user resource authorization on an owned recommendation.
"""
from __future__ import annotations

import uuid

import pytest

from app.core.auth import hash_password, issue_access_token
from app.models.auth import User
from app.models.recommendation import Recommendation, RecommendationWeight
from app.models.reference import Asset
from tests.conftest import test_session_factory as AsyncSessionLocal


def _uid() -> str:
    return str(uuid.uuid4())


async def _seed_owned_rec(owner_id: str | None) -> str:
    """Create a recommendation (optionally owned) with one weighted asset."""
    rec_id = _uid()
    asset_id = _uid()
    async with AsyncSessionLocal() as db:
        db.add(Asset(id=asset_id, ticker=f"OWN{rec_id[:4].upper()}", name="Owned Co"))
        db.add(Recommendation(
            id=rec_id, universe_id=_uid(), status="published", user_id=owner_id,
            model_confidence=0.8, data_confidence=0.9, operational_confidence=0.9,
        ))
        db.add(RecommendationWeight(
            id=_uid(), recommendation_id=rec_id, asset_id=asset_id,
            target_weight=1.0, stance="overweight",
        ))
        await db.commit()
    return rec_id


async def _make_user() -> tuple[str, dict[str, str]]:
    user_id = _uid()
    async with AsyncSessionLocal() as db:
        db.add(User(id=user_id, email=f"dpk-{user_id[:8]}@example.com",
                    password_hash=hash_password("x"), is_active=True))
        await db.commit()
    token, _ = issue_access_token(user_id=user_id, role="user")
    return user_id, {"Authorization": f"Bearer {token}"}


async def _get_seed_rec_id() -> str:
    """The conftest-seeded published recommendation (synthetic 'test' source)."""
    from sqlalchemy import select
    async with AsyncSessionLocal() as db:
        rec = (await db.execute(
            select(Recommendation).where(Recommendation.status == "published")
            .where(Recommendation.user_id.is_(None))
        )).scalars().first()
        return rec.id


@pytest.mark.asyncio
async def test_flag_off_hides_the_surface_with_404(client, monkeypatch):
    monkeypatch.setattr("app.api.v1.decision_packets.settings.feature_decision_packet_v1", False)
    rec_id = await _get_seed_rec_id()
    r = await client.get(f"/api/v1/recommendations/{rec_id}/decision-packets")
    assert r.status_code == 404, r.text


@pytest.mark.asyncio
async def test_flag_on_returns_bundle_with_explicit_outcomes(client, monkeypatch):
    monkeypatch.setattr("app.api.v1.decision_packets.settings.feature_decision_packet_v1", True)
    rec_id = await _get_seed_rec_id()
    r = await client.get(f"/api/v1/recommendations/{rec_id}/decision-packets")
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["recommendation_id"] == rec_id
    assert data["count"] >= 1
    assert data["policy_version"]
    # Seed market data uses source="test" → synthetic → honestly blocked.
    for packet in data["packets"]:
        assert packet["gate"]["outcome"] == "blocked"
        assert packet["gate"]["can_surface_decision"] is False
        assert packet["schema_version"] == "1.0"
    assert data["outcomes"].get("blocked", 0) == data["count"]


@pytest.mark.asyncio
async def test_flag_on_unknown_recommendation_is_404(client, monkeypatch):
    monkeypatch.setattr("app.api.v1.decision_packets.settings.feature_decision_packet_v1", True)
    r = await client.get("/api/v1/recommendations/does-not-exist/decision-packets")
    assert r.status_code == 404, r.text


@pytest.mark.asyncio
async def test_owner_can_read_own_recommendation_packets(client, monkeypatch):
    monkeypatch.setattr("app.api.v1.decision_packets.settings.feature_decision_packet_v1", True)
    owner_id, headers = await _make_user()
    rec_id = await _seed_owned_rec(owner_id)
    r = await client.get(f"/api/v1/recommendations/{rec_id}/decision-packets", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["data"]["recommendation_id"] == rec_id


@pytest.mark.asyncio
async def test_cross_user_cannot_read_owned_recommendation(client, monkeypatch):
    monkeypatch.setattr("app.api.v1.decision_packets.settings.feature_decision_packet_v1", True)
    owner_id, _ = await _make_user()
    _attacker_id, attacker_headers = await _make_user()
    rec_id = await _seed_owned_rec(owner_id)
    # Owned by someone else → 404 (existence not disclosed), even authenticated.
    r = await client.get(
        f"/api/v1/recommendations/{rec_id}/decision-packets", headers=attacker_headers
    )
    assert r.status_code == 404, r.text


@pytest.mark.asyncio
async def test_anonymous_cannot_read_owned_recommendation(client, monkeypatch):
    monkeypatch.setattr("app.api.v1.decision_packets.settings.feature_decision_packet_v1", True)
    owner_id, _ = await _make_user()
    rec_id = await _seed_owned_rec(owner_id)
    r = await client.get(f"/api/v1/recommendations/{rec_id}/decision-packets")
    assert r.status_code == 404, r.text
