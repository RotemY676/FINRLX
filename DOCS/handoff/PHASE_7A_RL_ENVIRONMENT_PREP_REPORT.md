# Phase 7A: RL / FINRL-X Environment Prep — Report

**Date:** 2026-04-25
**Phase:** 7A — Offline RL environment foundation
**Status:** Complete

---

## 1. Readiness Audit Summary

Full audit: `DOCS/handoff/PHASE_7A_RL_ENVIRONMENT_READINESS_AUDIT.md`

All prerequisites met: market_bars (90d, 10 assets), feature_values (8 keys), signal_outputs (3 deterministic + 1 ML shadow), backtest runner, policy rules (10), universe readiness, integration health. No blockers for offline RL environment construction.

---

## 2. Backend Files Changed

### Created (6)
```
backend/migrations/versions/014_rl_environment.py      — 4 RL tables
backend/app/models/rl.py                               — RLEnvironmentDefinition, RLEnvironmentRun, RLEpisode, RLStep
backend/app/services/rl_environment.py                 — RLEnvironmentService (state/action/reward/simulation)
backend/app/services/rl_agents.py                      — heuristic_baseline + random_valid agents
backend/app/api/v1/rl.py                               — 9 RL endpoints
backend/tests/test_phase7a_rl_environment.py           — 14 tests
```

### Modified (5)
```
backend/app/models/__init__.py   — registered RL models
backend/app/api/router.py        — registered rl_router
backend/app/api/v1/ops.py        — added RL block to /ops
backend/app/schemas/ops.py       — added OpsRLBlock
backend/seed.py                  — ensure default RL environment
```

---

## 3. Frontend Files Changed

### Modified (2)
```
frontend/src/services/api.ts        — added OpsRLBlock type
frontend/src/app/admin/page.tsx     — added RL Environment card
```

---

## 4. Tables Added (migration 014)

| Table | Key Columns |
|---|---|
| `rl_environment_definitions` | key, name, universe_id, state/action/reward/constraint_schema (JSON), status, is_shadow_only |
| `rl_environment_runs` | environment_key, run_type, agent_type, status, start/end_date, policy_snapshot, metrics |
| `rl_episodes` | environment_run_id, episode_index, initial/final_value, total_reward, total_return, max_drawdown, turnover, step_count |
| `rl_steps` | episode_id, step_index, as_of_date, state, action, reward, portfolio_value, cash_weight, exposure, constraint_violations |

---

## 5. Endpoints Added (9)

| Method | Path | Purpose |
|---|---|---|
| GET | `/rl/status` | RL environment status (shadow-only, live_influence=false) |
| GET | `/rl/environments` | List environment definitions |
| GET | `/rl/environments/{key}` | Single environment detail |
| POST | `/rl/environments/{key}/validate` | Validate environment readiness |
| POST | `/rl/simulations/run` | Run offline simulation |
| GET | `/rl/runs` | List simulation runs |
| GET | `/rl/runs/{run_id}` | Single run detail |
| GET | `/rl/runs/{run_id}/episodes` | Episodes in a run |
| GET | `/rl/episodes/{episode_id}/steps` | Steps in an episode |

---

## 6. RL Environment Schema

### State
- Asset prices from market_bars (as-of date, no lookahead)
- Deterministic engine scores (avg across technical_momentum, risk_quality, news_sentiment)
- Universe membership (tickers)
- Policy constraints (from policy_rules table)

### Action
- `target_weights`: dict of ticker→weight
- `cash_weight`: float
- `action_type`: "rebalance" or "no_op"

### Action Validation
- Weights sum + cash <= 1.0
- No negative weights
- Each position <= position_cap_max (default 0.15)
- Cash >= cash_floor (default 0.05)
- Total invested <= max_invested (default 0.95)
- All tickers must be in universe
- Violations are recorded, not silently ignored

### Reward
```
reward = portfolio_return - drawdown_penalty - turnover_penalty - violation_penalty

drawdown_penalty = |min(return, 0)| * 2.0
turnover_penalty = turnover * 0.001
violation_penalty = count(violations) * 0.05
```
This is a simple documented formula, not a final RL reward design.

---

## 7. Baseline Agents

| Agent | Type | Description |
|---|---|---|
| `heuristic_baseline` | Deterministic | Score-proportional allocation using engine signals, constrained by policy |
| `random_valid` | Stochastic | Random weights within policy constraints |

No neural network. No training loop. No external dependencies.

---

## 8. Offline Simulation Methodology

1. Generate weekly step dates from start to end
2. At each step: build state (prices, engine scores, universe, constraints)
3. Agent produces action (target weights)
4. Validate action against policy constraints
5. Compute portfolio return from price changes
6. Compute reward with penalties
7. Persist step (state, action, reward, portfolio_value, violations)
8. Track equity, drawdown, turnover across episode
9. Persist episode and run metrics

Same walk-forward pattern as BacktestService but at step/episode/run granularity for RL.

---

## 9. Why RL Remains Shadow/Offline

- `is_shadow_only=true` on all environment definitions
- `live_pipeline_influence=false` in status
- RL runs do not create Recommendation records
- RL runs do not appear in /recommendations/current or /overview
- RL does not write to signal_outputs consumed by pipeline
- /ops RL block clearly states shadow-only status
- Admin page shows "Offline / Shadow" and "Live influence: Off" badges

---

## Phase 7A.1 — Default Alias Resolution Addendum

**Date:** 2026-04-25

### Problem
- `POST /rl/environments/default/validate` returned "Environment not found"
- `POST /rl/simulations/run` with `environment_key="default"` ran but persisted `environment_key="default"` and `universe_id=null`

### Fix
1. Added `resolve_key()` method with alias map: `"default" → "quantpipeline_offline_v1"`
2. All key-accepting methods (`get_environment_definition`, `validate_environment`, `run_offline_simulation`) now resolve aliases before lookup
3. Canonical key is persisted, not the alias
4. Warning added when alias is used: "Environment alias 'default' resolved to 'quantpipeline_offline_v1'."
5. `universe_id` is always populated from the resolved environment definition

### Tests Added (4)
| Test | What It Verifies |
|---|---|
| `test_validate_default_alias` | Validate with "default" resolves to canonical key |
| `test_simulation_default_alias_persists_canonical` | Simulation persists canonical key + non-null universe_id |
| `test_simulation_has_universe_id` | universe_id is always populated |
| `test_real_key_still_works` | Canonical key works without alias warning |

### Test Output
```
256 passed, 2 skipped, 1 warning in 24.40s
```

---

## 10. Test Output

### Backend
```
$ python -m pytest tests/ -v
252 passed, 2 skipped, 1 warning in 20.51s

  14 new Phase 7A tests
  238 existing tests — all PASS (zero regressions)
```

### Frontend
```
$ npm run build
✓ Compiled successfully
✓ Generating static pages (11/11)
```

### Alembic + Seed
```
$ alembic upgrade head
Running upgrade 013_policy_rules -> 014_rl_env

$ python -m seed
RL: 1 new environment(s) created
```

---

## 11. Known Limitations

1. **90 days of data** — too short for meaningful RL training. More data needed for Phase 7B+.
2. **10 assets** — small universe. Real RL would need larger universe.
3. **No intraday data** — daily granularity only.
4. **Simple reward** — documented baseline formula, not optimized for RL performance.
5. **No multi-episode training** — single episode per run. Multi-episode/epoch support deferred.
6. **No model saving** — agents are stateless functions, no learned parameters.
7. **No benchmarking** — no comparison to buy-and-hold or index.
8. **State is compact** — only engine scores used, not full feature vectors.
9. **No transaction cost model** — turnover penalty approximates costs.

---

## 12. Recommended Next Phase Prompt

```
Phase 7B: [Future — RL Training Loop & FINRL-X Integration]
Prerequisites now met:
  - RL environment with state/action/reward definitions
  - Offline simulation with step-level persistence
  - Policy constraint validation
  - Baseline heuristic/random agents for benchmarking
  - Shadow-only governance enforced

Next steps:
  A. Multi-episode training loop with learned agents
  B. FINRL-X framework integration (stable-baselines3 / FinRL)
  C. Agent model persistence and versioning
  D. RL vs baseline comparison dashboard
  E. Extended data history for training
  F. Advanced reward function design

Do not start any without explicit instruction.
```
