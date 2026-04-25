# Phase 7B.1: RL Adapter & Policy Evaluation Truthfulness — Mini-Audit

**Date:** 2026-04-25

| Area | Status | Detail |
|---|---|---|
| Adapter file | FAIL | No rl_adapter.py exists; adapter logic split across rl_training.py and rl_environment.py |
| Train response shape | PASS | policy_snapshot_id now top-level (fixed in 7B hotfix) |
| Policy snapshot schema | PASS | JSON payload with weights, constraints, trained_on, notes |
| evaluate_policy behavior | FAIL | Calls run_offline_simulation("heuristic_baseline") — ignores stored policy_payload.weights |
| Evaluation labeling | FAIL | Returns agent_type="heuristic_baseline" for a score_weighted_baseline policy |
| Dataset export next_price | FAIL | No next_price, realized_return, or next_date fields |
| Adapter status fields | PARTIAL | Missing adapter_type, supports_*, no_broker_execution |

## Key Fixes Needed

1. **Create rl_adapter.py** — Gym-like reset/step/observe interface wrapping RLEnvironmentService
2. **Fix evaluate_policy** — must build agent from policy_payload.weights via _score_weighted_agent_fn, register it in AGENTS temporarily, run simulation with it
3. **Fix evaluation labeling** — agent_type must reflect policy source, include used_policy_weights=true
4. **Add next_price/realized_return to dataset export** — look ahead 1 day for next price; compute return
5. **Extend adapter status** — add capability fields
