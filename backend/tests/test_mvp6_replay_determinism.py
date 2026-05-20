"""Replay determinism harness.

Locks the contract that calling `ReplayService.create_replay_for_recommendation`
twice on the same Recommendation produces byte-identical snapshot payloads,
ignoring the snapshot's own primary key and `captured_at`.

If this test fails, something on the pipeline started embedding non-deterministic
state in `snapshot_data` — e.g. `datetime.now()`, a fresh UUID, or a payload
whose JSON serialization isn't sort-stable.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime

import pytest
from sqlalchemy import select

from app.models.recommendation import Recommendation
from app.services.replay import ReplayService
from tests.conftest import test_session_factory

_UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def _project(snapshots) -> list[tuple[str, str]]:
    """Stable projection of a snapshot list — drops id and captured_at."""
    return sorted(
        (snap.stage, json.dumps(snap.snapshot_data, sort_keys=True, default=str))
        for snap in snapshots
    )


def _hash(projection: list[tuple[str, str]]) -> str:
    blob = "\n".join(f"{stage}|{payload}" for stage, payload in projection)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _looks_like_fresh_uuid(value: object) -> bool:
    return isinstance(value, str) and bool(_UUID_RE.match(value))


def _walk_for_non_determinism(node: object) -> list[str]:
    """Find any value in snapshot_data that looks like it could be a fresh
    per-call UUID or timestamp. Returns a list of human-readable findings.

    This is a heuristic — a legitimate stored UUID (e.g. `recommendation_id`)
    will also match. The test does NOT fail on this list alone; the hash
    equality is the gate. The list is logged on failure to help the operator
    triage.
    """
    findings: list[str] = []

    def visit(path: str, value: object) -> None:
        if isinstance(value, dict):
            for k, v in value.items():
                visit(f"{path}.{k}" if path else str(k), v)
        elif isinstance(value, list):
            for i, v in enumerate(value):
                visit(f"{path}[{i}]", v)
        elif _looks_like_fresh_uuid(value):
            findings.append(f"{path}={value} (UUID-shaped)")
        elif isinstance(value, datetime):
            findings.append(f"{path}={value.isoformat()} (datetime)")

    visit("", node)
    return findings


@pytest.mark.asyncio
async def test_replay_two_calls_produce_identical_payload(setup_db):
    """The hard contract: re-running replay does not perturb snapshot_data."""
    async with test_session_factory() as db:
        rec_id = (await db.execute(
            select(Recommendation.id).order_by(Recommendation.created_at.desc()).limit(1)
        )).scalar_one_or_none()
        assert rec_id is not None, "conftest must seed at least one Recommendation"

        svc = ReplayService(db)
        first = await svc.create_replay_for_recommendation(rec_id)
        assert first, "first replay produced no snapshots — the seed pipeline data is incomplete"
        proj_first = _project(first)
        hash_first = _hash(proj_first)

    async with test_session_factory() as db:
        svc = ReplayService(db)
        second = await svc.create_replay_for_recommendation(rec_id)
        assert second
        proj_second = _project(second)
        hash_second = _hash(proj_second)

    if hash_first != hash_second:
        # Show where they diverged so the failure is debuggable.
        diff = []
        for (s1, p1), (s2, p2) in zip(proj_first, proj_second, strict=False):
            if s1 != s2 or p1 != p2:
                diff.append(f"stage={s1} vs {s2}\n  first:  {p1}\n  second: {p2}")
        pytest.fail(
            "Replay produced different payloads between two calls.\n"
            f"First hash:  {hash_first}\n"
            f"Second hash: {hash_second}\n"
            f"Diff:\n" + "\n".join(diff[:5])
        )


@pytest.mark.asyncio
async def test_replay_snapshot_count_matches_pipeline_stages(setup_db):
    """A regression guard for the pipeline-stage count.

    Seed data has selection + allocation + timing + risk + recommendation = 5 stages.
    If a new stage is added to the pipeline and the seed updates, this test must
    be updated to match.
    """
    async with test_session_factory() as db:
        rec_id = (await db.execute(
            select(Recommendation.id).order_by(Recommendation.created_at.desc()).limit(1)
        )).scalar_one_or_none()
        svc = ReplayService(db)
        snapshots = await svc.create_replay_for_recommendation(rec_id)

    stages = sorted({s.stage for s in snapshots})
    assert stages == ["allocation", "recommendation", "risk_overlay", "selection", "timing"]


@pytest.mark.asyncio
async def test_replay_snapshot_data_has_no_loose_timestamps(setup_db):
    """No naked datetime objects should land in `snapshot_data` — they must be
    serialized to strings or stored as DB columns elsewhere. A loose datetime
    is the most common source of nondeterminism between two replays of the
    same recommendation.
    """
    async with test_session_factory() as db:
        rec_id = (await db.execute(
            select(Recommendation.id).order_by(Recommendation.created_at.desc()).limit(1)
        )).scalar_one_or_none()
        svc = ReplayService(db)
        snapshots = await svc.create_replay_for_recommendation(rec_id)

    for s in snapshots:
        findings = _walk_for_non_determinism(s.snapshot_data)
        datetime_findings = [f for f in findings if "(datetime)" in f]
        assert not datetime_findings, (
            f"stage={s.stage} contains a naked datetime in snapshot_data: {datetime_findings}"
        )
