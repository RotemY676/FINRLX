---
name: replay-determinism-harness
description: Locks the contract that re-running ReplayService on the same Recommendation produces byte-identical snapshot payloads. Catches non-deterministic serialization, time-dependent fields leaking into snapshot_data, and random IDs sneaking into the payload (beyond the snapshot's own primary key).
type: project
---

# Replay Determinism Harness

A FINRLX-internal test contract: a `Recommendation` must replay the same way today and tomorrow.

## What this protects

Replays are how the operator (and a regulator, if it ever comes to that) reconstructs *why* a recommendation was made. If the replay payload drifts between calls — because a service started embedding `datetime.now()`, or because Python dict iteration order leaks into a JSON blob, or because a new field defaults to a fresh UUID — the audit trail is broken.

This skill encodes a single, hard contract:

> For a given `Recommendation`, two successive calls to `ReplayService.create_replay_for_recommendation` MUST produce snapshot payloads (`snapshot_data` + `stage`) that hash to the same value, after stripping the snapshot's own `id` and `captured_at` (which are necessarily fresh per call).

## When to invoke

- On any change to `app/services/replay.py`.
- On any change to a service whose output is captured in a snapshot (`SelectionRun`, `AllocationResult`, `TimingResult`, `RiskOverlayResult`, `Recommendation`).
- On any change to a Pydantic / SQLAlchemy field that becomes part of `snapshot_data`.
- Before cutting a release tag.

## How to apply

The harness lives in `backend/tests/test_mvp6_replay_determinism.py`. It uses the existing in-memory test DB and the seed Recommendation from `conftest.py`. The test does:

1. Resolve the seeded `Recommendation` id.
2. Call `ReplayService.create_replay_for_recommendation(rec_id)` twice.
3. For each call, build a deterministic projection:
   ```python
   projection = sorted(
       (snap.stage, json.dumps(snap.snapshot_data, sort_keys=True, default=str))
       for snap in snapshots
   )
   ```
4. Hash and compare.
5. Also assert that no field inside any `snapshot_data` matches a "fresh-UUID" or "fresh-timestamp" shape between the two calls.

## What this skill does NOT do

- Does not re-run the upstream pipeline (selection → allocation → timing → risk) from input data. Replay determinism is a weaker but achievable contract; full pipeline determinism is MVP-7+ scope and depends on the recommendation-object-provenance work landing in MVP-3.
- Does not check that the payload is *correct*, only that it is *stable*. Correctness is `BacktestHygieneGate` + the existing service-level tests.
- Does not check timing / performance.

## How to extend

When a new pipeline stage is added (e.g. "rebalance_smoothing"):

1. Update `ReplayService.create_replay_for_recommendation` to emit a snapshot for it.
2. Add the corresponding seed data to `conftest.py`.
3. The existing test will pick up the new stage automatically because the projection iterates over the full snapshot list.

## Failure mode

If this test fails, the diff message will show which `(stage, snapshot_data)` pair changed between calls. Common offenders:

- `datetime.now()` accidentally embedded in `snapshot_data`.
- `uuid.uuid4()` used inside `snapshot_data` (the snapshot's own `id` is fine; nested UUIDs are not).
- Iteration over a dict whose ordering is implementation-defined (CPython is insertion-ordered, but tests sometimes catch this on PyPy or with `dict(sorted(...))` being missed).
- A new field whose default is `Field(default_factory=...)` with a non-pure factory.
