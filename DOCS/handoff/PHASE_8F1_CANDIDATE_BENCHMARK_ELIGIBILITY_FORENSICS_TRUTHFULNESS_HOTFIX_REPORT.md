# Phase 8F.1: Candidate Benchmark Eligibility, Forensics & Truthfulness Hotfix

**Date:** 2026-04-26
**Status:** Complete

---

## Root Cause

Four gaps in Phase 8F: (1) eligibility check too weak, (2) missing forensic_summary_by_agent, (3) include_baselines=false still included score_weighted_baseline, (4) inference_mode wording was misleading.

## GAP 1 — Eligibility Changes

`check_benchmark_eligibility()` now validates ALL of:

**Artifact metadata:**
- `imported_from_artifact == true`
- `artifact_hash` exists
- `artifact_summary` exists

**Safety flags (from candidate dict):**
- `not_eligible_for_promotion == true`
- `research_only == true`
- `offline_only == true`
- `shadow_only == true`
- `live_pipeline_influence == false`
- `no_broker_execution == true`
- `no_publication_influence == true`
- `no_recommendation_pollution == true`

**Stored payload verification:**
- `policy_payload.safety_flags.research_only == true`
- `policy_payload.safety_flags.no_broker_execution == true`
- `policy_payload.imported_from_artifact == true`

**Isolation checks:**
- `promotion_blocked == true`
- `publication_blocked == true`
- `live_recommendation_blocked == true`
- `overview_influence_blocked == true`
- `broker_execution_blocked == true`
- `all_blocked == true`

Each failed condition returns a specific rejection reason.

## GAP 2 — forensic_summary_by_agent

Candidate benchmark response now includes `forensic_summary_by_agent` pulled from `report_obj.dataset_lineage["forensic_summary_by_agent"]`. Contains per-agent forensic rows keyed by agent name (including the `imported_candidate:` surrogate).

## GAP 3 — include_baselines Behavior

**Decision: Option A — truthful candidate-only mode.**

Added `ensure_score_weighted_baseline: bool = True` parameter to `RLBenchmarkService.run_benchmark()`. Default `True` preserves existing behavior. Candidate benchmarks pass `ensure_score_weighted_baseline=include_baselines`:

| `include_baselines` | Executed agents |
|---------------------|----------------|
| `true` | surrogate + heuristic_baseline + random_valid + score_weighted_baseline |
| `false` | surrogate only |

Existing benchmark callers are unchanged (default `ensure_score_weighted_baseline=True`).

## GAP 4 — Inference Mode Wording

**Decision: Option A — truthful rename.**

| Field | Old value | New value |
|-------|-----------|-----------|
| `inference_mode` | `"surrogate_metadata_only"` | `"score_weighted_fallback_surrogate"` |
| `real_neural_inference` | `false` | `false` (unchanged) |
| `artifact_metadata_used_for_inference` | (not present) | `false` |
| `surrogate_description` | (not present) | `"Deterministic score-weighted fallback. No neural model loaded."` |

Updated in: response context, audit events, benchmark history, warnings.

## Files Changed

```
backend/app/services/finrlx_research.py   — eligibility, forensics, inference_mode, include_baselines
backend/app/services/rl_benchmark.py       — ensure_score_weighted_baseline parameter
backend/tests/test_phase8f_candidate_benchmark.py — rewritten with 24 tests
DOCS/handoff/PHASE_8F1_CANDIDATE_BENCHMARK_ELIGIBILITY_FORENSICS_TRUTHFULNESS_HOTFIX_REPORT.md
```

## Tests Added/Updated (24 total)

- `test_eligibility_checks_all_safety_flags` — validates comprehensive checks
- `test_benchmark_include_baselines_false` — surrogate only, no baselines
- `test_benchmark_include_baselines_true_includes_all_three` — all 3 baselines
- `test_benchmark_context_inference_mode` — truthful inference_mode and fields
- `test_benchmark_warnings_mention_fallback` — warning text
- `test_benchmark_has_forensic_summary_by_agent` — forensic per-agent
- Plus existing eligibility, run, isolation, fingerprint, audit, history, safety tests

## Backend Test Results

```
425 passed, 2 skipped — zero regressions
```

## Frontend Status

Not touched.

## Design Handoff Review

No UI changes. Design files reviewed in Phase 8F. Existing backtests patterns handle surrogate agent display.

## Safety Confirmations

| Check | Status |
|-------|--------|
| No live RL | CONFIRMED |
| No broker execution | CONFIRMED |
| No recommendation pollution | CONFIRMED |
| No overview pollution | CONFIRMED |
| No publication influence | CONFIRMED |
| No production dependency changes | CONFIRMED |
| No neural inference in production | CONFIRMED |
| Benchmarks research/offline/shadow only | CONFIRMED |

## Production Smoke Commands

```powershell
$base = "https://backend-production-aab8.up.railway.app/api/v1"

# Import candidate
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
$import = Invoke-RestMethod "$base/rl/finrlx/import-research-artifact" -Method POST -ContentType "application/json" -Body (@{ artifact = $artifact; import_acknowledgement = $true; source = "smoke_8f1" } | ConvertTo-Json -Depth 20)
$cid = $import.data.policy_candidate_id

# Eligibility
$elig = Invoke-RestMethod "$base/rl/finrlx/candidates/$cid/benchmark-eligibility"
$elig.data.eligible  # Expected: true

# Benchmark with baselines
$r = Invoke-RestMethod "$base/rl/finrlx/candidates/$cid/benchmark" -Method POST -ContentType "application/json" -Body (@{ start_date = "2026-03-15"; end_date = "2026-04-15"; include_baselines = $true; research_acknowledgement = $true } | ConvertTo-Json)
$r.data.candidate_benchmark_context.inference_mode  # Expected: score_weighted_fallback_surrogate
$r.data.candidate_benchmark_context.real_neural_inference  # Expected: false
$r.data.candidate_benchmark_context.artifact_metadata_used_for_inference  # Expected: false
$r.data.forensic_summary_by_agent.PSObject.Properties.Name
$r.data.executed_agents  # Should include imported_candidate:... + 3 baselines

# Benchmark without baselines
$r2 = Invoke-RestMethod "$base/rl/finrlx/candidates/$cid/benchmark" -Method POST -ContentType "application/json" -Body (@{ start_date = "2026-03-15"; end_date = "2026-04-15"; include_baselines = $false; research_acknowledgement = $true } | ConvertTo-Json)
$r2.data.executed_agents  # Should only include imported_candidate:...

# History
Invoke-RestMethod "$base/rl/finrlx/candidates/$cid/benchmarks"

# Regression
$b = Invoke-RestMethod "$base/rl/benchmarks/run" -Method POST -ContentType "application/json" -Body '{"start_date":"2026-03-15","end_date":"2026-04-15"}'
$b.data.status  # Expected: completed
```

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Eligibility checks all safety flags | PASS |
| 2 | Rejects unsafe candidates | PASS |
| 3 | Response includes forensic_summary_by_agent | PASS |
| 4 | include_baselines=false is truthful | PASS |
| 5 | include_baselines=true includes all 3 | PASS |
| 6 | inference_mode=score_weighted_fallback_surrogate | PASS |
| 7 | real_neural_inference=false | PASS |
| 8 | artifact_metadata_used_for_inference=false | PASS |
| 9 | Audit uses truthful inference_mode | PASS |
| 10 | History uses truthful inference_mode | PASS |
| 11 | Phase 8E import tests pass | PASS |
| 12 | Phase 8C/8B tests pass | PASS |
| 13 | Normal benchmark works | PASS |
| 14 | /rl/execute 404 | PASS |
| 15 | /overview unaffected | PASS |
| 16 | /recommendations/current unaffected | PASS |
| 17 | /publication/status unaffected | PASS |
| 18 | No production dep changes | PASS |
| 19 | No neural inference | PASS |
| 20 | Backend tests pass (425) | PASS |
| 21 | Frontend if touched | N/A |
| 22 | Design reviewed | PASS |
