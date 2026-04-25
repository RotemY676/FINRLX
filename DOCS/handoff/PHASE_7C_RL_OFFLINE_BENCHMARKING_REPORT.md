# Phase 7C: RL Offline Benchmarking & Forensic Comparison — Report

**Date:** 2026-04-25
**Phase:** 7C — Offline benchmarking, agent comparison, forensic analysis
**Status:** Complete

---

## 1. Executive Summary

Phase 7C adds an offline RL benchmarking layer that compares multiple agents on the same dataset window, producing persisted reports with per-agent metrics, reward component breakdowns, violation tracking, and step-level forensic summaries. All outputs are explicitly labeled offline/shadow-only with comprehensive safety flags.

---

## 2. Files Changed

### Created (4)
```
backend/migrations/versions/016_rl_benchmarks.py     — rl_benchmark_reports table
backend/app/services/rl_benchmark.py                 — RLBenchmarkService
backend/app/api/v1/rl_benchmark.py                   — 4 benchmark endpoints
backend/tests/test_phase7c_rl_benchmarking.py        — 18 tests
DOCS/handoff/PHASE_7C_RL_OFFLINE_BENCHMARKING_REPORT.md
```

### Modified (6)
```
backend/app/models/rl.py             — added RLBenchmarkReport model
backend/app/models/__init__.py       — registered RLBenchmarkReport
backend/app/api/router.py            — registered rl_benchmark_router
backend/app/api/v1/ops.py            — merged benchmark data into RL ops block
backend/app/schemas/ops.py           — added total_benchmarks, latest_benchmark_status to OpsRLBlock
frontend/src/services/api.ts         — extended OpsRLBlock type
frontend/src/app/admin/page.tsx      — added benchmarks count + latest status to RL card
```

---

## 3. Schema Changes

### Migration 016: rl_benchmark_reports

| Column | Type | Notes |
|---|---|---|
| id | String(36) PK | |
| name | String(200) | Benchmark label |
| environment_key | String(80) | |
| universe_id | String(36) | nullable |
| start_date, end_date | Date | Benchmark window |
| status | String(20) | completed/partial/failed |
| compared_agents | JSON | List of agent keys |
| metrics_by_agent | JSON | Per-agent: total_return, total_reward, max_drawdown, turnover, step_count, violations |
| reward_breakdown_by_agent | JSON | Per-agent: portfolio_return, drawdown_penalty, turnover_penalty |
| violations_by_agent | JSON | Per-agent violation lists (capped at 20 per agent) |
| forensic_summary | JSON | Step-level rows (capped at 100) |
| simulation_run_ids | JSON | Per-agent simulation run ID mapping |
| policy_snapshot_ids | JSON | Policy snapshots included |
| dataset_lineage | JSON | Environment key + date range |
| safety_flags | JSON | All 6 safety flags |
| warnings | JSON | |
| created_at, completed_at | DateTime | |

---

## 4. API Endpoints Added (4)

| Method | Path | Purpose |
|---|---|---|
| POST | `/rl/benchmarks/run` | Run benchmark comparing multiple agents |
| GET | `/rl/benchmarks` | List benchmark reports |
| GET | `/rl/benchmarks/{id}` | Single benchmark report |
| POST | `/rl/benchmarks/compare-policy` | Compare a policy snapshot against baselines |

---

## 5. Benchmark Service Behavior

1. Resolves environment key (handles aliases)
2. Determines agent list (defaults: heuristic_baseline, random_valid, score_weighted_baseline)
3. Optionally registers policy snapshot agents from stored weights
4. Runs each agent's simulation on the same date window via `RLEnvironmentService.run_offline_simulation()`
5. Collects per-agent metrics, reward breakdowns, violations
6. Produces step-level forensic summary (first agent, up to 100 rows)
7. Persists complete report with safety flags
8. Cleans up temporary agent registrations

---

## 6. Compared Agents

| Agent | Type | Source |
|---|---|---|
| heuristic_baseline | Deterministic | Score-proportional allocation |
| random_valid | Stochastic | Random constrained weights |
| score_weighted_baseline | Deterministic | Grid-search calibrated blend |
| policy_{snapshot_id} | From snapshot | Stored policy_payload.weights |

---

## 7. Example Benchmark Output (structure)

```json
{
  "id": "...",
  "name": "Offline Agent Comparison",
  "status": "completed",
  "compared_agents": ["heuristic_baseline", "random_valid", "score_weighted_baseline"],
  "metrics_by_agent": {
    "heuristic_baseline": {"total_return": 0.023, "total_reward": 0.019, "max_drawdown": -0.01, "total_turnover": 1.2, "step_count": 5, "violation_count": 0},
    "random_valid": {"total_return": -0.005, "total_reward": -0.012, ...},
    "score_weighted_baseline": {"total_return": 0.023, ...}
  },
  "reward_breakdown_by_agent": {
    "heuristic_baseline": {"portfolio_return_component": 0.023, "drawdown_penalty_component": 0.02, "turnover_penalty_component": 0.0012}
  },
  "forensic_summary": [
    {"step_index": 0, "as_of_date": "2026-03-17", "agent_key": "heuristic_baseline", "reward": 0.0, "portfolio_value": 100.0, "turnover": 0.95}
  ],
  "safety_flags": {
    "offline_only": true,
    "shadow_only": true,
    "live_pipeline_influence": false,
    "no_broker_execution": true,
    "no_publication_influence": true,
    "no_recommendation_pollution": true
  }
}
```

---

## 8. Safety Guarantees

- **No live RL** — all simulations are offline walk-forward
- **No broker execution** — no trading APIs, no order placement, no credentials
- **No auto-trading** — no automated execution of any kind
- **No publication influence** — benchmark reports do not affect publication state machine
- **No recommendation pollution** — benchmark does not create Recommendation records
- **No overview pollution** — /overview is unaffected
- **No live decision pipeline influence** — engines, pipeline, and signals are unaffected
- All benchmark outputs include explicit `safety_flags` JSON with all 6 flags

---

## 9. Tests Run

### Backend
```
299 passed, 2 skipped, 1 warning in 33.36s

  18 new Phase 7C tests
  281 existing tests — all PASS (zero regressions)
```

### Phase 7C Tests (18)
| Test | Verifies |
|---|---|
| test_benchmark_creates_report | Report created with 3+ agents |
| test_benchmark_includes_metrics_by_agent | Per-agent return/reward/drawdown/turnover |
| test_benchmark_includes_reward_breakdown | Portfolio return, drawdown, turnover components |
| test_benchmark_includes_safety_flags | All 6 safety flags present |
| test_benchmark_includes_forensic_summary | Step-level rows with dates/reward/value |
| test_benchmark_includes_violations | Per-agent violation counts |
| test_benchmark_includes_warnings | Warnings list or null |
| test_benchmark_is_persisted | Read by ID after creation |
| test_benchmark_list | List endpoint works |
| test_compare_policy | Policy snapshot compared against baselines |
| test_benchmark_insufficient_data | Short window doesn't crash |
| test_benchmark_does_not_affect_recommendations | /current unaffected |
| test_benchmark_does_not_affect_overview | /overview unaffected |
| test_publication_unchanged | Publication status unaffected |
| test_no_broker_execution_endpoint | /rl/execute returns 404 |
| test_rl_benchmark_outputs_shadow | Safety flags in output |
| test_ops_includes_benchmark_info | /ops RL block has benchmark fields |
| test_pipeline_still_works | Full pipeline still operates |

---

## 10. Frontend Build/Lint Result

```
✓ Compiled successfully
✓ Generating static pages (11/11)

Route (app)
├ ○ /admin                               6.54 kB        96.7 kB
... all pages compiled
```

---

## 11. Production Smoke Commands

```powershell
$base = "https://backend-production-aab8.up.railway.app/api/v1"

# 1. RL adapter status
Invoke-RestMethod "$base/rl/adapter/status"

# 2. Run benchmark
Invoke-RestMethod -Method Post -Uri "$base/rl/benchmarks/run" -ContentType "application/json" -Body '{"start_date":"2026-03-15","end_date":"2026-04-15"}'

# 3. List benchmarks
Invoke-RestMethod "$base/rl/benchmarks"

# 4. Read specific benchmark (replace ID)
# Invoke-RestMethod "$base/rl/benchmarks/<benchmark_id>"

# 5. Policy evaluation still works
# Invoke-RestMethod -Method Post -Uri "$base/rl/policies/<snapshot_id>/evaluate" -ContentType "application/json" -Body '{}'

# 6. Overview still safe
Invoke-RestMethod "$base/overview"

# 7. Recommendations still safe
Invoke-RestMethod "$base/recommendations/current"

# 8. Ops includes benchmark info
(Invoke-RestMethod "$base/ops").data.rl
```

---

## 12. Known Limitations

1. **Forensic summary limited to first agent** — only first compared agent gets step-level rows (to control report size)
2. **Violations capped at 20 per agent** — prevents unbounded JSON storage
3. **90 days of data** — short for meaningful comparison; heuristic and score_weighted produce identical results with current data
4. **No cross-metric ranking** — no automatic "best agent" determination
5. **No chart rendering** — benchmark data is JSON only; no equity curve visualization for comparison yet
6. **No temporal train/eval split** — benchmark runs all agents on same full window

---

## 13. Design Handoff Review

**Design files reviewed:**
- `design/handoff-package/HANDOFF.md` — product architecture, 4 lanes, component inventory
- `design/handoff-package/INDEX.md` — quick reference and getting started
- `design/handoff-package/tokens.css` — oklch color tokens (canvas, surface, ink, pos, caution, breach)
- `design/handoff-package/styles.css` — card system, KPI strip, table conventions, badge styles
- `design/handoff-package/Ops.html` — command center layout with KPI strip + section cards
- `design/handoff-package/Design System.html` — component patterns and typography hierarchy

**Relevant UI patterns found:**
- KPI metric cards: `text-[14px] font-semibold font-mono` value + `text-[10px] text-ink-4` label
- Section cards: `rounded-lg border border-line bg-surface p-pad shadow-sm`
- Status badges: `inline-flex px-2 py-0.5 rounded-md text-[10px] font-medium` with semantic bg colors
- Grid layout: responsive `grid-cols-2 sm:grid-cols-N lg:grid-cols-N gap-3`

**Patterns reused:**
- Admin RL card follows exact same card/grid/badge pattern as ML Observability, Policy Rules, Integrations, Universe cards
- "Offline / Shadow" badge uses existing `bg-surface-3 text-ink-3` token
- "Live influence: Off" badge uses same pattern

**UI work added:**
- Extended RL card in Admin/Ops with `total_benchmarks` count and `latest_benchmark_status`
- No new components created; all existing design patterns reused

---

## 14. Recommended Next Phase

```
Phase 7D: [Future — FINRL-X Neural Training & Advanced Agents]
Prerequisites now met:
  - RL environment with state/action/reward
  - Agent registry with 3 agents
  - Training harness with policy snapshots
  - Gym-like adapter with reset/step
  - Dataset export with next_price/realized_return
  - Offline benchmarking with forensic comparison
  - Safety governance enforced

Next steps:
  A. FINRL-X / stable-baselines3 integration
  B. PPO/A2C/SAC agents with GPU-optional training
  C. Multi-episode training with train/eval split
  D. Benchmark comparison dashboard (equity curves, charts)
  E. Extended data history (>90d)
  F. Advanced reward function design

Do not start any without explicit instruction.
```
