# Phase 8F: Imported Research Candidate Benchmark Evaluation

**Date:** 2026-04-26
**Status:** Complete

---

## Executive Summary

Phase 8F enables imported FinRL-X research candidates to be evaluated by the existing offline benchmark layer alongside baseline agents. The imported candidate runs as a deterministic surrogate (score-weighted) since production cannot execute real neural inference. All benchmark outputs are clearly labeled as research-only, offline, shadow, with no production influence.

## Files Changed

```
EDIT backend/app/services/finrlx_research.py         — check_benchmark_eligibility(), run_candidate_benchmark(), get_candidate_benchmarks()
EDIT backend/app/api/v1/rl_finrlx.py                 — 3 new endpoints + 1 request model
NEW  backend/tests/test_phase8f_candidate_benchmark.py — 19 tests
NEW  DOCS/handoff/PHASE_8F_IMPORTED_RESEARCH_CANDIDATE_BENCHMARK_EVALUATION_REPORT.md
```

No frontend changes. No production dependency changes.

## Backend Changes

### Service: `FinRLXResearchService`

**`check_benchmark_eligibility(candidate_id) -> dict`**
- Checks candidate exists, is imported from artifact, has artifact_hash, and has research_only safety flags
- Returns: `{eligible, reasons, candidate_summary, safety_flags, isolation_checks}`

**`run_candidate_benchmark(candidate_id, name, start_date, end_date, include_baselines) -> dict`**
- Validates eligibility first (rejects with audit event if ineligible)
- Registers a temporary surrogate agent (`imported_candidate:<id>`) using `_score_weighted_agent_fn({})` — deterministic score-proportional allocation
- Calls existing `RLBenchmarkService.run_benchmark()` with surrogate + baseline agents
- Captures production fingerprints before/after
- Creates audit events (requested + completed)
- Cleans up temporary agent registration in `finally` block
- Returns full benchmark report with `candidate_benchmark_context`

**`get_candidate_benchmarks(candidate_id) -> list[dict]`**
- Queries completed benchmark audit events filtered by candidate_id
- Returns list of benchmark summaries with report IDs, fingerprints, inference mode

## API Endpoints Added

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/rl/finrlx/candidates/{id}/benchmark-eligibility` | GET | Check if candidate can be benchmarked |
| `/rl/finrlx/candidates/{id}/benchmark` | POST | Run offline benchmark for candidate |
| `/rl/finrlx/candidates/{id}/benchmarks` | GET | List candidate's benchmark history |

## Frontend/UI Changes

**None.** Existing admin benchmark UI already displays agent comparison tables, metrics, forensic drill-downs, and safety badges. The surrogate agent appears alongside baselines with its `imported_candidate:` key. No new UI components needed.

## Design Handoff Review

**Files reviewed:** HANDOFF.md, Backtests.html, Ops.html, Design System.html, styles.css, tokens.css, ops.css, backtests.css

**UI touched:** No.

**Why reviewed:** Confirmed existing backtests UI patterns (equity curves, tear sheets, metric tables, per-agent tabs) are suitable for displaying imported candidate benchmark results. The surrogate agent appears as another agent row in existing tables. No new design patterns needed.

## Candidate Eligibility Behavior

Eligible if:
- Candidate exists
- `imported_from_artifact == true`
- `artifact_hash` exists
- `safety_flags.research_only == true`

Rejected if:
- Candidate not found
- Not imported from artifact (e.g., train-research stub candidates)
- Missing artifact_hash

## Candidate-to-Agent Adapter Behavior

The surrogate agent is created via `_score_weighted_agent_fn({})` — the same factory used by existing policy snapshot benchmarks. It produces deterministic score-proportional allocations respecting policy constraints (position_cap, cash_floor, max_invested).

Agent key: `imported_candidate:<candidate_id_prefix>`

The surrogate is registered temporarily in the global `AGENTS` dict and removed in a `finally` block after the benchmark completes.

## Inference Mode Truthfulness

- `inference_mode: "surrogate_metadata_only"`
- `real_neural_inference: false`
- Warning: "No neural inference was run in production."
- Warning: "Benchmark uses deterministic score-weighted surrogate adapter."

Production does NOT load torch models or run neural forward passes. The surrogate is a deterministic heuristic.

## Benchmark Behavior

1. Requires `research_acknowledgement=true` (422 otherwise)
2. Validates dates (malformed → 422, reversed → 422)
3. Checks candidate eligibility (rejected → 422 + audit event)
4. Registers surrogate agent temporarily
5. Calls existing `RLBenchmarkService.run_benchmark()` with surrogate + baseline agents
6. Returns standard benchmark report shape with additional `candidate_benchmark_context`
7. Includes `metrics_by_agent`, `reward_breakdown_by_agent`, `forensic_summary`
8. Includes `result_fingerprint` and `invariant_check_results`

## Candidate Benchmark History Behavior

`GET /candidates/{id}/benchmarks` returns list of completed benchmark summaries queried from audit events, including benchmark_report_id, artifact_hash, inference_mode, executed_agents, result_fingerprint.

## Audit Event Behavior

| Event | When |
|-------|------|
| `finrlx_candidate_benchmark_requested` | Benchmark starts for eligible candidate |
| `finrlx_candidate_benchmark_completed` | Benchmark finishes with report |
| `finrlx_candidate_benchmark_rejected` | Candidate fails eligibility |

Completed event includes: candidate_id, artifact_hash, benchmark_report_id, surrogate_key, inference_mode, executed_agents, isolation_checks, component_checks, production_fingerprints_unchanged, result_fingerprint.

## Production Fingerprint Behavior

Captured before and after benchmark:
- `recommendations_current`: unchanged=true
- `publication_status`: unchanged=true
- `overview`: snapshot_available=false with reason
- Overall: unchanged=true (benchmark only creates RLBenchmarkReport + simulation records)

## Tests Run

```
420 passed, 2 skipped — zero regressions
```

Phase 8F tests (19):
- 3 eligibility tests (missing, non-imported, imported)
- 3 validation tests (acknowledgement, malformed dates, reversed dates)
- 6 benchmark run tests (baselines, context, isolation, fingerprints, audit, history)
- 7 safety regression tests

## Backend Test Results

All 420 tests pass.

## Frontend Build Status

Not touched.

## Production Smoke Commands

```powershell
$base = "https://backend-production-aab8.up.railway.app/api/v1"

# Import a candidate (or use existing)
$artifact = @{
  artifact_type = "finrlx_cpu_rl_research_artifact"; schema_version = "1.0"
  research_only = $true; offline_only = $true; shadow_only = $true
  not_eligible_for_promotion = $true; live_pipeline_influence = $false
  no_broker_execution = $true; no_publication_influence = $true; no_recommendation_pollution = $true
  algorithm = "PPO"; real_neural_training = $true; cpu_only = $true; synthetic_data = $true
  dataset_summary = @{ row_count = 60; synthetic = $true }
  training_config = @{ algorithm = "PPO"; timesteps = 200; seed = 42 }
  training_metrics = @{ timesteps = 200; algorithm = "PPO"; seed = 42; total_reward = 0.01 }
  artifact_created_at = "2026-04-26T00:00:00Z"
  warnings = @("Synthetic smoke artifact.")
}
$import = Invoke-RestMethod "$base/rl/finrlx/import-research-artifact" -Method POST -ContentType "application/json" -Body (@{ artifact = $artifact; import_acknowledgement = $true; source = "smoke_8f" } | ConvertTo-Json -Depth 20)
$cid = $import.data.policy_candidate_id

# Check eligibility
Invoke-RestMethod "$base/rl/finrlx/candidates/$cid/benchmark-eligibility"

# Benchmark without ack → 422
try { Invoke-RestMethod "$base/rl/finrlx/candidates/$cid/benchmark" -Method POST -ContentType "application/json" -Body (@{ start_date = "2026-03-15"; end_date = "2026-04-15" } | ConvertTo-Json) } catch { $_.Exception.Response.StatusCode.value__ }

# Run benchmark
$r = Invoke-RestMethod "$base/rl/finrlx/candidates/$cid/benchmark" -Method POST -ContentType "application/json" -Body (@{ name = "Phase 8F Smoke"; start_date = "2026-03-15"; end_date = "2026-04-15"; include_baselines = $true; research_acknowledgement = $true } | ConvertTo-Json)
$r.data.status
$r.data.candidate_benchmark_context | ConvertTo-Json -Depth 8
$r.data.executed_agents
$r.data.metrics_by_agent.PSObject.Properties.Name

# Benchmark history
Invoke-RestMethod "$base/rl/finrlx/candidates/$cid/benchmarks"

# Safety
try { Invoke-RestMethod "$base/rl/execute" -Method POST -ContentType "application/json" -Body "{}" } catch { $_.Exception.Response.StatusCode.value__ }
Invoke-RestMethod "$base/overview"
Invoke-RestMethod "$base/recommendations/current"
Invoke-RestMethod "$base/publication/status"

# Existing benchmark regression
$b = Invoke-RestMethod "$base/rl/benchmarks/run" -Method POST -ContentType "application/json" -Body '{"start_date":"2026-03-15","end_date":"2026-04-15"}'
$b.data.status
```

## Known Limitations

1. Surrogate agent uses score-weighted heuristic, not real neural policy — clearly labeled
2. No real torch model loading in production (by design)
3. Candidate benchmark history queries audit events (not a dedicated relation table)
4. No frontend UI changes (deferred — existing admin benchmark UI handles display)
5. Duplicate benchmarks for same candidate are allowed (no dedup)

## Stop/Go Recommendation for Phase 8G

**GO** — Phase 8F completes the research artifact lifecycle: local training (8D) → import (8E) → benchmark (8F). Phase 8G could focus on:
1. Admin UI enhancements for artifact import and candidate benchmark visualization
2. Dataset export streamlining (one-click export for local training)
3. Benchmark comparison improvements (imported vs baseline side-by-side)
4. Documentation and operator runbook

## Safety Confirmations

| Check | Status |
|-------|--------|
| No live RL | CONFIRMED |
| No broker execution | CONFIRMED |
| No auto-trading | CONFIRMED |
| No recommendation pollution | CONFIRMED |
| No overview pollution | CONFIRMED |
| No publication influence | CONFIRMED |
| No production dependency changes | CONFIRMED |
| No neural inference in production | CONFIRMED |
| Imported candidate benchmarks research/offline/shadow only | CONFIRMED |
| All candidates not_eligible_for_promotion | CONFIRMED |

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Benchmark eligibility endpoint exists | PASS |
| 2 | Benchmark run endpoint exists | PASS |
| 3 | Benchmark history endpoint exists | PASS |
| 4 | Missing candidate rejected | PASS |
| 5 | Non-imported candidate rejected | PASS |
| 6 | Imported candidate accepted | PASS |
| 7 | Requires research_acknowledgement | PASS |
| 8 | Validates malformed dates | PASS |
| 9 | Rejects reversed dates | PASS |
| 10 | Includes baseline agents | PASS |
| 11 | Includes surrogate agent | PASS |
| 12 | Includes candidate_benchmark_context | PASS |
| 13 | real_neural_inference=false | PASS |
| 14 | inference_mode=surrogate_metadata_only | PASS |
| 15 | Includes isolation_checks | PASS |
| 16 | Includes production_fingerprints | PASS |
| 17 | Audit events persisted | PASS |
| 18 | Benchmark history returns report | PASS |
| 19 | not_eligible_for_promotion=true | PASS |
| 20 | /rl/execute unavailable | PASS |
| 21 | /recommendations/current unaffected | PASS |
| 22 | /overview unaffected | PASS |
| 23 | /publication/status unaffected | PASS |
| 24 | Existing benchmark works | PASS |
| 25 | Existing benchmark audit works | PASS |
| 26 | Existing import works | PASS |
| 27 | Phase 8A/8B/8C endpoints work | PASS |
| 28 | No production dependency changes | PASS |
| 29 | No neural inference added | PASS |
| 30 | No live RL/broker/rec/overview/pub | PASS |
| 31 | Backend tests pass (420 passed) | PASS |
| 32 | Frontend if touched | N/A |
| 33 | Design reviewed | PASS |
| 34 | Smoke commands included | PASS |
| 35 | No unsafe language | PASS |
