# Phase 7B: RL Offline Training Harness / FINRL-X Adapter Prep — Report

**Date:** 2026-04-25
**Phase:** 7B — Agent registry, training harness, policy snapshots, dataset export
**Status:** Complete

---

## 1. Audit Summary

Full audit: `DOCS/handoff/PHASE_7B_RL_TRAINING_HARNESS_AUDIT.md`

Phase 7A environment (state/action/reward/simulation) was fully ready. Missing: agent registry, training loop, policy snapshot persistence, dataset export, adapter status. All implemented in 7B.

---

## 2. Backend Files Changed

### Created (5)
```
backend/migrations/versions/015_rl_training.py            — 3 tables (agents, training_runs, policy_snapshots)
backend/app/services/rl_training.py                       — RLTrainingService (train, evaluate, export, adapter status)
backend/app/api/v1/rl_training.py                         — 10 training endpoints
backend/tests/test_phase7b_rl_training_harness.py         — 14 tests
DOCS/handoff/PHASE_7B_RL_TRAINING_HARNESS_REPORT.md
```

### Modified (7)
```
backend/app/models/rl.py             — added RLAgentDefinition, RLTrainingRun, RLPolicySnapshot
backend/app/models/__init__.py       — registered new models
backend/app/api/router.py            — registered rl_training_router
backend/app/api/v1/ops.py            — merged env + training data into RL ops block
backend/app/schemas/ops.py           — extended OpsRLBlock with training fields
backend/seed.py                      — ensure 3 default agent definitions
frontend/src/services/api.ts         — extended OpsRLBlock type
frontend/src/app/admin/page.tsx      — extended RL card with agents/training/snapshots
```

---

## 3. Tables Added (migration 015)

| Table | Key Columns |
|---|---|
| `rl_agent_definitions` | key, name, agent_type, algorithm_family, status, is_trainable, is_shadow_only, config_schema |
| `rl_training_runs` | agent_key, environment_key, status, train/eval dates, config, metrics, model_artifact_ref |
| `rl_policy_snapshots` | training_run_id, agent_key, environment_key, policy_type, policy_payload (JSON), metrics |

---

## 4. Endpoints Added (10)

| Method | Path | Purpose |
|---|---|---|
| GET | `/rl/agents` | List agent definitions |
| GET | `/rl/agents/{key}` | Single agent detail |
| GET | `/rl/adapter/status` | Adapter status (offline_only, shadow_only, counts) |
| GET | `/rl/dataset/export` | Export training dataset rows |
| POST | `/rl/train` | Train baseline agent (grid search) |
| GET | `/rl/training-runs` | List training runs |
| GET | `/rl/training-runs/{id}` | Training run detail |
| GET | `/rl/policies` | List policy snapshots |
| GET | `/rl/policies/{id}` | Single policy snapshot |
| POST | `/rl/policies/{id}/evaluate` | Evaluate policy on date range |

---

## 5. Adapter Design

The adapter wraps RLEnvironmentService methods:
- **State:** `build_state(as_of_date)` — prices, engine scores, universe, policy constraints
- **Action validation:** `validate_action(action, state)` — cap, floor, universe checks
- **Reward:** `compute_reward(...)` — return - drawdown - turnover - violations
- **Dataset export:** daily rows with ticker/price/score/constraints

No external Gym dependency. Internal Gym-like interface pattern.

---

## 6. Dataset Export Schema

Each row:
```json
{
  "as_of_date": "2026-03-15",
  "universe_tickers": ["AAPL", "MSFT", ...],
  "policy_constraints": {"position_cap_max": 0.15, ...},
  "assets": [
    {"ticker": "AAPL", "price": 195.5, "engine_score": 0.72},
    ...
  ]
}
```

---

## 7. Baseline Training Methodology

**Agent:** `score_weighted_baseline`
**Algorithm:** `deterministic_grid_search`
**Process:**
1. Run heuristic_baseline simulation over training period
2. Record baseline reward/return
3. Persist calibrated blend weights as policy snapshot

**Policy snapshot format:**
```json
{
  "weights": {"technical_momentum": 0.40, "risk_quality": 0.35, "news_sentiment": 0.25},
  "constraints": {...},
  "trained_on": {"start_date": "...", "end_date": "...", "step_count": N},
  "notes": "baseline grid-search policy, not neural RL"
}
```

This is NOT neural RL. It's a deterministic calibration baseline.

---

## 8. Default Agents

| Agent | Type | Trainable | Algorithm |
|---|---|---|---|
| `heuristic_baseline` | Deterministic | No | Score-proportional |
| `random_valid` | Stochastic | No | Uniform random |
| `score_weighted_baseline` | Deterministic | Yes | Grid search |

All agents: `is_shadow_only=true`, no neural networks, no GPU.

---

## 9. Test Output

### Backend
```
270 passed, 2 skipped, 1 warning in 23.07s

  14 new Phase 7B tests
  256 existing tests — all PASS
```

### Frontend
```
✓ Compiled successfully
✓ Generating static pages (11/11)
```

### Alembic + Seed
```
Running upgrade 014_rl_env -> 015_rl_train
RL Agents: 3 new agent(s) created
```

---

## 10. Known Limitations

1. **90 days of data** — baseline "training" is a single simulation, not a true grid search across many weight combos
2. **No neural training** — deliberately excluded; baseline only
3. **No model persistence** — policy snapshots are JSON, not binary model files
4. **No multi-episode training** — single episode per training run
5. **No benchmarking** — no comparison to buy-and-hold baseline yet
6. **Dataset export is per-request** — no file export; paginated JSON only
7. **Agent functions are stateless** — trained policy snapshots don't yet create custom agent callables for evaluation

---

## 11. Recommended Next Phase Prompt

```
Phase 7C: [Future — FINRL-X Integration & Advanced Training]
Prerequisites now met:
  - RL environment with state/action/reward
  - Agent registry with 3 agents (1 trainable)
  - Training harness with policy snapshots
  - Dataset export for external training
  - Offline simulation with step-level persistence
  - Shadow-only governance enforced

Next steps:
  A. FINRL-X / stable-baselines3 integration (optional external dep)
  B. Multi-episode training with proper train/eval split
  C. Advanced reward function design
  D. Policy snapshot → custom agent callable for evaluation
  E. RL vs baseline comparison dashboard
  F. Extended data history (>90d)
  G. GPU-optional PPO/A2C/SAC agents

Do not start any without explicit instruction.
```
