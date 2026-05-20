# Phase MVP-3 — Recommendation Provenance

**Date:** 2026-05-20
**Branch:** main
**Parent commit (MVP-2):** 34688d5

## Summary

Every Recommendation emitted by the decision pipeline now carries four tamper-evident
provenance fields:

- `input_hash` — SHA-256 of canonical JSON over the SignalOutput rows used
- `policy_hash` — SHA-256 of canonical JSON over the pipeline policy constants
- `pipeline_version` — semantic version string of the pipeline
- `replay_seed` — UUID generated per run (informational today; threads through any
  future RNG)

The Recommendation Object is the project's canonical output, and now it's also the
project's auditable contract. This unlocks the Replay screen (MVP-4+) as a real
trust feature: an operator can re-run the pipeline against a stored Recommendation
and assert the hashes still match.

## Test Evidence

| Suite | Before MVP-3 | After MVP-3 |
|---|---|---|
| Backend pytest total | 688 passed, 2 skipped | **706 passed, 2 skipped, 0 failed** (~280s) |
| New `tests/test_mvp3_recommendation_provenance.py` | — | 18 tests (16 pure-function, 2 integration against real pipeline) |
| Frontend | untouched | untouched |

## What Was Added

### New backend files
- `backend/app/services/provenance.py` — `PIPELINE_VERSION`, `compute_input_hash`,
  `compute_policy_hash`, `new_replay_seed`, `verify_provenance`, `canonical_signal_row`,
  `_sha256_canonical`, `_json_safe`
- `backend/migrations/versions/019_recommendation_provenance.py` — adds 4 columns
  on `recommendations` (all nullable for backward compat) + index on `input_hash`
- `backend/tests/test_mvp3_recommendation_provenance.py` — 18 tests:
  - 16 pure-function tests: order independence, byte-identity, sensitivity to
    score/stance/artifact changes, policy changes, UUID seed uniqueness,
    verify_provenance happy + mismatch paths
  - 2 integration tests against the real pipeline: provenance fields populated;
    policy_hash + pipeline_version stable across runs while replay_seed differs

### New project-local skill
- `.claude/skills/recommendation-object-provenance/SKILL.md` — codifies the rule
  ("every recommendation must have all four fields") for future agents working on
  pipeline.py, engines.py, or any code path that emits Recommendations

### Modified files
- `backend/app/models/recommendation.py` — added 4 columns: `input_hash`,
  `policy_hash`, `pipeline_version`, `replay_seed` (all nullable Mapped[str | None])
- `backend/app/services/pipeline.py`:
  - imports from `app.services.provenance`
  - `_policy_snapshot()` helper returns the dict hashed into `policy_hash`
  - `run_pipeline` sets `input_hash`, `pipeline_version`, `replay_seed` at rec
    creation time (eagerly, before stages run, so the hash binds to immutable
    inputs)
  - `generate_recommendation` accepts an explicit `signal_outputs` param and
    computes `input_hash` only if not already set; sets `policy_hash` at the end

## Architecture

```
run_pipeline(...)
   ├─ _get_registered_signals()           ──> outputs: list[SignalOutput]
   ├─ rec = Recommendation(
   │       pipeline_version=PIPELINE_VERSION,
   │       replay_seed=new_replay_seed(),
   │       input_hash=compute_input_hash(outputs),     ◄── EAGER
   │   )
   ├─ stages (selection, allocation, timing, risk overlay) ── do NOT mutate outputs
   └─ generate_recommendation(..., signal_outputs=outputs)
          └─ rec.policy_hash = compute_policy_hash(_policy_snapshot())
                                ▲
                                │ at write time, locks in current policy
```

The eager-hash-at-entry pattern ensures that whatever happens during stage
execution cannot drift the input binding. This was the highest-severity finding
from the code review and is now structural.

## Provenance Contract

| Field | Source | Determinism Guarantee |
|---|---|---|
| `input_hash` | `compute_input_hash(SignalOutputs)` | Order-independent; byte-identical for byte-identical canonical fields (signal_run_id, asset_id, score, stance, confidence, artifacts) |
| `policy_hash` | `compute_policy_hash(_policy_snapshot())` | Order-independent; byte-identical for byte-identical policy constants |
| `pipeline_version` | `PIPELINE_VERSION` constant | Must be bumped on any change to deterministic behavior |
| `replay_seed` | `new_replay_seed()` UUID | Per-run unique; threaded through future RNG paths |

## Code Review Triage

A single combined `code-reviewer + simplify` agent found 8 issues. Triage:

**Applied this phase:**

1. **HIGH — `replay_seed` double-write footgun.** The seed was set at rec
   creation AND conditionally overwritten in `generate_recommendation`. Fixed:
   single-source assignment at creation only.
2. **MEDIUM — `_provenance_inputs` stash on ORM instance was a leaky
   abstraction.** Replaced with an explicit `signal_outputs` parameter on
   `generate_recommendation`. Also added eager `input_hash` computation at
   pipeline entry (before stages run) so the hash window is closed entirely.
3. **MEDIUM — Skill frontmatter `type: project-local` is non-standard.**
   Replaced with `source: project` to match catalog convention.
4. **LOW — `noqa: E731` lambda for the getter dispatch.** Replaced with two
   explicit branches (dict.get vs getattr).

**Deferred:**

| # | Finding | Defer to | Reason |
|---|---|---|---|
| D1 | `verify_provenance` is dead code in `backend/` | MVP-4 | Intentionally pre-wired for the Replay endpoint; tests exercise it |
| D2 | `PIPELINE_VERSION` is a string literal with no validation | never | Typo on bump is caught by tests asserting `rec.pipeline_version == PIPELINE_VERSION` |
| D3 | `_json_safe` falls through to `str(o)` for unknown types | MVP-5 | Adding `raise TypeError` is an opinionated change; today payloads are SQLAlchemy floats only |
| D4 | Integration tests couple to `tests.conftest.test_session_factory` | next test cleanup | Same pattern used elsewhere in the suite |

## Skill Activation Discipline (Phase MVP-3)

Invoked via `Skill` tool at phase start:
- `quant-analyst` — informed the choice of what counts as "input" to the rec
  (signal scores + stances + confidences + artifacts, not just signal_run_id)
- `backtesting-frameworks` — informed the need for a `pipeline_version` bump
  rule and explicit `replay_seed` even when no RNG is in use today

Cross-cutting (loaded earlier, active here):
- `verification-before-completion` — gate honored
- `code-reviewer + /simplify` — single combined agent (right-sized for the
  small surface); 8 findings, 4 applied / 4 deferred with documented reasons
- `architect-review` — informed the no-breaking-change scope (all new fields
  nullable; existing pipeline tests pass unchanged)
- `commit` — drove commit format

## Built: Project-Local Skill

`.claude/skills/recommendation-object-provenance/SKILL.md` is the first
project-local skill. Future agents working on pipeline.py / engines.py will
load this and have a concrete rule (the "iron rule" + how-to-apply guidance)
for what counts as provenance-affecting code.

## What MVP-3 Does NOT Do (intentional)

- No frontend wiring. The Replay screen will use `verify_provenance` in MVP-4.
- No backfill. Existing Recommendations have all four fields NULL.
- No enforcement at API level. `generate_recommendation` still works without
  `signal_outputs`; in that case `input_hash` is left NULL. The current
  pipeline always passes it, so the integration tests verify it's populated.
- No Monte Carlo / sampling. The `replay_seed` is generated and stored but
  no RNG path uses it yet.

## Gate Result

| Gate | Status | Evidence |
|---|---|---|
| All previous tests still pass | ✅ | 688 → still 688 passing; 18 new MVP-3 tests added |
| Pure-function provenance tests | ✅ | 16 tests (order independence, byte-identity, sensitivity to score/stance/artifact/policy changes, seed uniqueness, verify happy/mismatch) |
| Integration tests against real pipeline | ✅ | 2 tests (provenance populated; policy_hash + pipeline_version stable across runs) |
| Code-reviewer + simplify pass | ✅ | 8 findings, 4 applied, 4 deferred with documented reasons |
| Project-local skill registered | ✅ | `.claude/skills/recommendation-object-provenance/SKILL.md` |

**Phase MVP-3 status: COMPLETE.** Ready to push and advance to MVP-4 (Onboarding + Feature Flags).
