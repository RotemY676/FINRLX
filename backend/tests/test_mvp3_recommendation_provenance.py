"""Phase MVP-3 — Recommendation provenance / replay determinism harness.

Contract for the provenance module:

  Same logical inputs              ->  byte-identical input_hash
  Mutated input (1 byte / 1 float) ->  different input_hash
  Mutated policy constant          ->  different policy_hash
  Re-running the pipeline twice    ->  the rec carries provenance fields
                                       and they verify via verify_provenance

These are pure-function tests against app.services.provenance and a single
integration test that exercises the real pipeline twice and compares.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.services.provenance import (
    PIPELINE_VERSION,
    canonical_signal_row,
    compute_input_hash,
    compute_policy_hash,
    new_replay_seed,
    verify_provenance,
)


# ───────── pure-function tests ──────────────────────────────────────────────


def _row(signal_run_id, asset_id, score, stance="hold", confidence=0.5, artifacts=None):
    return SimpleNamespace(
        signal_run_id=signal_run_id,
        asset_id=asset_id,
        score=score,
        stance=stance,
        confidence=confidence,
        artifacts=artifacts or {},
    )


def test_canonical_signal_row_accepts_dict_and_namespace_identically():
    ns = _row("r1", "a1", 0.5, "buy", 0.9)
    d = {"signal_run_id": "r1", "asset_id": "a1", "score": 0.5, "stance": "buy", "confidence": 0.9, "artifacts": {}}
    assert canonical_signal_row(ns) == canonical_signal_row(d)


def test_compute_input_hash_is_order_independent():
    rows = [
        _row("r1", "a1", 0.5),
        _row("r1", "a2", 0.3),
        _row("r2", "a1", 0.7),
    ]
    h1 = compute_input_hash(rows)
    h2 = compute_input_hash(list(reversed(rows)))
    assert h1 == h2


def test_compute_input_hash_is_byte_identical_across_calls():
    rows = [_row("r1", "a1", 0.5), _row("r1", "a2", 0.3)]
    assert compute_input_hash(rows) == compute_input_hash(rows)


def test_compute_input_hash_changes_when_score_changes_by_epsilon():
    rows_a = [_row("r1", "a1", 0.5), _row("r1", "a2", 0.3)]
    rows_b = [_row("r1", "a1", 0.5000001), _row("r1", "a2", 0.3)]
    assert compute_input_hash(rows_a) != compute_input_hash(rows_b)


def test_compute_input_hash_changes_when_stance_changes():
    rows_a = [_row("r1", "a1", 0.5, stance="buy")]
    rows_b = [_row("r1", "a1", 0.5, stance="sell")]
    assert compute_input_hash(rows_a) != compute_input_hash(rows_b)


def test_compute_input_hash_changes_when_artifacts_change():
    rows_a = [_row("r1", "a1", 0.5, artifacts={"ticker": "AAPL"})]
    rows_b = [_row("r1", "a1", 0.5, artifacts={"ticker": "MSFT"})]
    assert compute_input_hash(rows_a) != compute_input_hash(rows_b)


def test_compute_policy_hash_byte_identical_across_calls():
    p = {"a": 1, "b": 2.5, "c": 0.95}
    assert compute_policy_hash(p) == compute_policy_hash(p)


def test_compute_policy_hash_order_independent():
    p1 = {"a": 1, "b": 2.5}
    p2 = {"b": 2.5, "a": 1}
    assert compute_policy_hash(p1) == compute_policy_hash(p2)


def test_compute_policy_hash_changes_on_value_change():
    p1 = {"MAX_POSITION_WEIGHT": 0.15}
    p2 = {"MAX_POSITION_WEIGHT": 0.16}
    assert compute_policy_hash(p1) != compute_policy_hash(p2)


def test_compute_policy_hash_changes_on_new_key():
    p1 = {"MAX_POSITION_WEIGHT": 0.15}
    p2 = {"MAX_POSITION_WEIGHT": 0.15, "NEW_KNOB": 1.0}
    assert compute_policy_hash(p1) != compute_policy_hash(p2)


def test_new_replay_seed_is_uuid_string():
    s = new_replay_seed()
    parsed = uuid.UUID(s)  # must not raise
    assert str(parsed) == s


def test_new_replay_seed_is_unique_per_call():
    seeds = {new_replay_seed() for _ in range(100)}
    assert len(seeds) == 100


def test_verify_provenance_ok_when_hashes_match():
    ok, mismatches = verify_provenance("aaa", "bbb", "aaa", "bbb")
    assert ok is True
    assert mismatches == []


def test_verify_provenance_reports_input_mismatch():
    ok, mismatches = verify_provenance("aaa", "bbb", "XXX", "bbb")
    assert ok is False
    assert any("input_hash mismatch" in m for m in mismatches)


def test_verify_provenance_reports_policy_mismatch():
    ok, mismatches = verify_provenance("aaa", "bbb", "aaa", "YYY")
    assert ok is False
    assert any("policy_hash mismatch" in m for m in mismatches)


def test_verify_provenance_reports_both_mismatches():
    ok, mismatches = verify_provenance("aaa", "bbb", "XXX", "YYY")
    assert ok is False
    assert len(mismatches) == 2


# ───────── integration test against the real pipeline ───────────────────────


async def _ensure_signals(client) -> str:
    """Same pattern as Phase 4D tests — compute features, then run engines."""
    from datetime import date
    today = date.today().isoformat()
    r = await client.post("/api/v1/features/compute", json={"as_of": today})
    fs_id = r.json()["data"]["feature_set_id"]
    await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})
    return fs_id


@pytest.mark.asyncio
async def test_pipeline_recommendation_carries_provenance_fields(client):
    """Run the real pipeline; the resulting recommendation has all four provenance fields set."""
    fs_id = await _ensure_signals(client)
    r = await client.post("/api/v1/pipeline/run", json={"feature_set_id": fs_id})
    assert r.status_code == 200, r.text
    body = r.json()["data"]
    rec_id = body["recommendation_id"]
    assert rec_id is not None, body

    from sqlalchemy import select
    from app.models.recommendation import Recommendation
    from tests.conftest import test_session_factory as AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        rec = (await db.execute(select(Recommendation).where(Recommendation.id == rec_id))).scalar_one()

    assert rec.input_hash is not None, "input_hash must be set after pipeline run"
    assert len(rec.input_hash) == 64, "input_hash should be SHA-256 hex (64 chars)"
    assert rec.policy_hash is not None, "policy_hash must be set after pipeline run"
    assert len(rec.policy_hash) == 64
    assert rec.pipeline_version == PIPELINE_VERSION
    assert rec.replay_seed is not None
    uuid.UUID(rec.replay_seed)


@pytest.mark.asyncio
async def test_two_pipeline_runs_with_same_signals_have_identical_policy_and_pipeline_version(client):
    """Determinism: policy_hash + pipeline_version are stable; replay_seed differs."""
    from sqlalchemy import select
    from app.models.recommendation import Recommendation
    from tests.conftest import test_session_factory as AsyncSessionLocal

    fs_id_1 = await _ensure_signals(client)
    r1 = await client.post("/api/v1/pipeline/run", json={"feature_set_id": fs_id_1})
    rec_id_1 = r1.json()["data"]["recommendation_id"]

    fs_id_2 = await _ensure_signals(client)
    r2 = await client.post("/api/v1/pipeline/run", json={"feature_set_id": fs_id_2})
    rec_id_2 = r2.json()["data"]["recommendation_id"]

    assert rec_id_1 != rec_id_2

    async with AsyncSessionLocal() as db:
        rec1 = (await db.execute(select(Recommendation).where(Recommendation.id == rec_id_1))).scalar_one()
        rec2 = (await db.execute(select(Recommendation).where(Recommendation.id == rec_id_2))).scalar_one()

    # Policy + pipeline version are absolute and must match.
    assert rec1.policy_hash == rec2.policy_hash
    assert rec1.pipeline_version == rec2.pipeline_version
    # Replay seeds are per-run, must differ.
    assert rec1.replay_seed != rec2.replay_seed
