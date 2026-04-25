# Phase 7C.1: Benchmark Truthfulness Hotfix — Report

**Date:** 2026-04-25
**Status:** Complete

---

## Root Cause

`score_weighted_baseline` was defined as an agent definition in `rl_training.py` (DEFAULT_AGENTS) and had its logic in `_score_weighted_agent_fn`, but was **never registered in the `AGENTS` dict** in `rl_agents.py`. The benchmark service checks `if agent_key not in AGENTS` and skips unknown agents, so `score_weighted_baseline` was always skipped in production.

## Files Changed (5)

```
backend/app/services/rl_agents.py        — registered score_weighted_baseline_agent in AGENTS dict
backend/app/services/rl_benchmark.py     — track executed/skipped agents; status=partial when agents skipped
backend/app/api/v1/rl_benchmark.py       — expose requested_agents, executed_agents, skipped_agents, is_complete_comparison
backend/tests/test_phase7c1_benchmark_truthfulness.py — 7 new tests
DOCS/handoff/PHASE_7C1_BENCHMARK_TRUTHFULNESS_HOTFIX_REPORT.md
```

## Tests Run

```
306 passed, 2 skipped, 1 warning (37.91s)
  7 new Phase 7C.1 tests + 299 existing — zero regressions
```

## Production Smoke Commands

```powershell
$base = "https://backend-production-aab8.up.railway.app/api/v1"

# Benchmark with all three agents
$r = Invoke-RestMethod -Method Post -Uri "$base/rl/benchmarks/run" -ContentType "application/json" -Body '{"start_date":"2026-03-15","end_date":"2026-04-15"}'
$r.data.status                           # should be "completed"
$r.data.is_complete_comparison            # should be True
$r.data.compared_agents                   # should include score_weighted_baseline
$r.data.metrics_by_agent.PSObject.Properties.Name  # should include all 3
$r.data.skipped_agents                    # should be empty

# Safety unchanged
$r.data.safety_flags
Invoke-RestMethod "$base/recommendations/current"
Invoke-RestMethod "$base/overview"
```

## Confirmations

- **score_weighted_baseline included in metrics_by_agent:** CONFIRMED
- **partial/completed status is truthful:** CONFIRMED (partial when agents skipped, completed when all run)
- **design/handoff-package reviewed:** CONFIRMED (no UI style changes needed)
- **RL remains offline/shadow only:** CONFIRMED
