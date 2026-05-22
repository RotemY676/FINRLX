---
name: recommendation-object-provenance
description: Enforce that every Recommendation emitted by the FINRLX pipeline is tamper-evident and replayable. Use when modifying pipeline.py, decision_pipeline models, the engines layer, or when adding any new code path that mutates a Recommendation prior to publication.
type: project
---

# FINRLX — Recommendation Object Provenance

## Use this skill when

- Touching `backend/app/services/pipeline.py` (the decision pipeline)
- Touching `backend/app/services/engines.py` or any code that emits SignalOutput rows
- Adding or modifying any field on `Recommendation` or `RecommendationWeight`
- Adding new policy constants that influence selection/allocation/timing/risk overlay
- Building a Monte-Carlo or sampling step that introduces randomness
- Adding a new data provider that contributes to the inputs hashed into `input_hash`
- Working on the Replay screen or its API

## Do not use this skill when

- You are only fixing styling or non-functional code paths
- You are touching auth, ingestion, or other services that don't change Recommendation outputs

## Iron rule

Every Recommendation must, before it is committed to the DB:

1. Set `input_hash` — SHA-256 of canonical JSON of the SignalOutput rows used
2. Set `policy_hash` — SHA-256 of canonical JSON of the policy constants in effect
3. Set `pipeline_version` — the `PIPELINE_VERSION` constant from `app.services.provenance`
4. Set `replay_seed` — a UUID generated per run (informational today; threaded through any RNG you add)

If any of these fields would be `None` for a non-trivial recommendation, the pipeline is broken.

## How to apply

- `compute_input_hash(signal_rows)` accepts ORM rows or dicts; both yield the same hash for the same logical inputs.
- `compute_policy_hash(policy_dict)` is just `sha256(canonical_json(policy_dict))`. If you add a new policy constant, **add it to `_policy_snapshot()` in `pipeline.py`** or the hash silently misses the change.
- `PIPELINE_VERSION` in `provenance.py` MUST be bumped whenever you change the pipeline's deterministic behavior (selection / allocation / timing / risk overlay logic). Failure to bump = silent reproducibility break.
- If your code introduces randomness (e.g. Monte Carlo), use `replay_seed` to seed your RNG. Storing `replay_seed` without threading it through is worthless.

## Why

- Reg/legal: an algorithmically-generated investment recommendation must be reproducible on audit (SEC 2026 priorities on automated tools).
- Operational: when a tester says "this rec looked wrong yesterday," the operator must be able to replay it deterministically.
- Trust: the Replay screen is a public-facing trust feature; if it ever shows different output than the original, user trust collapses.

## Determinism harness

`backend/tests/test_mvp3_recommendation_provenance.py` is the contract. Any change that breaks these tests is a regression. Specifically:

- **Same inputs → byte-identical `input_hash`**. Re-runs of the same signal set hash identically regardless of insertion order.
- **Mutate one signal score by ε → `input_hash` changes**. The pipeline notices any input drift.
- **Mutate one policy constant → `policy_hash` changes**. Policy drift is detected.
- **Stored hashes verify via `verify_provenance`**.

## When in doubt

If you're not sure whether a code change you're making should affect the hashes:

- Adds a NEW input that influences the recommendation → include it in `canonical_signal_row` or `_policy_snapshot()`.
- Adds a feature that is purely cosmetic (e.g. response shape, logging text) → do not touch provenance.
- Removes an existing input (e.g. dropping a signal field) → bump `PIPELINE_VERSION`.
- Changes ordering / sorting of signals inside the pipeline → no hash change required (`compute_input_hash` is order-independent by design).
