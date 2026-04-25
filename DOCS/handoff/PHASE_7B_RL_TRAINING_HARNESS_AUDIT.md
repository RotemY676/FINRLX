# Phase 7B: RL Training Harness — Implementation Audit

**Date:** 2026-04-25

---

| Area | Status | Detail |
|---|---|---|
| RL environment schema | PASS | 4 tables: definitions, runs, episodes, steps |
| RL run/episode/step persistence | PASS | Full step-level JSON state/action/reward |
| State fields | PASS | prices, engine_scores, tickers, policy_constraints |
| Action validation | PASS | position_cap, cash_floor, max_invested, universe-only |
| Reward computation | PASS | return - drawdown - turnover - violations |
| Data coverage | PARTIAL | 90 days, 10 assets — enough for baseline, short for real RL |
| Agent support | PARTIAL | heuristic_baseline + random_valid exist; no trainable agent |
| Policy integration | PASS | policy_rules read into constraints |
| Gym-style adapter | FAIL | No reset/step/observation interface yet |
| Dataset export | FAIL | No export of state/price/return rows |
| Agent registry | FAIL | No rl_agent_definitions table |
| Training harness | FAIL | No train/evaluate/policy_snapshot persistence |

## Answers

- **Can we build a safe offline adapter now?** Yes — build_state, validate_action, compute_reward all exist.
- **What is missing for real RL training?** Agent registry, training loop, policy snapshot, evaluation harness. No neural nets needed for baseline.
- **What can be simulated deterministically?** Score-weighted grid search over engine blend weights.
- **Which limitations must be visible?** "baseline grid-search, not neural RL", "90d data", "offline-only".
- **How do we keep RL from affecting live pipeline?** is_shadow_only=true, no recommendation creation, no publication, no signal_output writes.
