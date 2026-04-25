# Phase 7B.1: RL Adapter & Policy Evaluation Truthfulness Hardening — Report

**Date:** 2026-04-25
**Phase:** 7B.1 — Adapter, evaluation truthfulness, dataset export
**Status:** Complete

---

## 1. Files Changed

### Created (3)
```
backend/app/services/rl_adapter.py                              — RLAdapter (Gym-like reset/step/observe)
backend/tests/test_phase7b1_rl_adapter_policy_truthfulness.py   — 11 tests
DOCS/handoff/PHASE_7B1_RL_ADAPTER_POLICY_EVALUATION_AUDIT.md
DOCS/handoff/PHASE_7B1_RL_ADAPTER_POLICY_EVALUATION_HARDENING_REPORT.md
```

### Modified (1)
```
backend/app/services/rl_training.py   — evaluate_policy uses stored weights; dataset export adds next_price/realized_return; adapter status adds capability fields
```

---

## 2. Fixes Applied

### Policy evaluation truthfulness
**Before:** `evaluate_policy()` called `run_offline_simulation("heuristic_baseline")` — ignored stored policy weights, returned `agent_type="heuristic_baseline"`.

**After:** Builds agent function from `policy_payload.weights` via `_score_weighted_agent_fn()`, registers as temporary agent, runs simulation with it. Response includes:
- `used_policy_weights: true`
- `policy_type: "score_weighted_blend"`
- `policy_weights: {"technical_momentum": 0.40, ...}`
- If payload is invalid, falls back to heuristic with explicit warning.

### Dataset export enrichment
**Before:** Rows had `ticker`, `price`, `engine_score` only.

**After:** Each asset row includes:
- `next_price` — price on next trading day (null if unavailable)
- `realized_return` — `(next_price - price) / price` (null if unavailable)
- `warnings` per row if next_price is missing

Each row includes:
- `next_date` — the next trading day date

### Adapter status enrichment
**Before:** Basic counts and shadow flags.

**After:** Includes:
- `adapter_type: "internal_gym_like"`
- `supports_reset_step: true`
- `supports_dataset_export: true`
- `supports_policy_evaluation: true`
- `no_broker_execution: true`

### RL Adapter service
New `RLAdapter` class with Gym-like interface:
- `reset(environment_key, start_date, end_date)` → observation
- `step(action)` → (observation, reward, done, info)
- `get_observation()`, `get_action_space()`, `get_observation_schema()`, `get_reward_schema()`
- `get_adapter_info()` — static capabilities

---

## 3. Test Output

```
281 passed, 2 skipped, 1 warning in 28.73s

  11 new Phase 7B.1 tests
  270 existing tests — all PASS
```

### Phase 7B.1 Tests (11)

| Test | What It Verifies |
|---|---|
| `test_adapter_status_includes_capabilities` | All safety/capability fields present |
| `test_adapter_reset_step` | Internal adapter reset/step works |
| `test_dataset_export_includes_next_price` | next_price, realized_return in export |
| `test_train_response_has_top_level_policy_snapshot_id` | Top-level policy_snapshot_id |
| `test_evaluate_uses_policy_weights` | Evaluation uses stored weights, used_policy_weights=true |
| `test_evaluate_labels_policy_truthfully` | Labels match policy source |
| `test_invalid_policy_returns_fallback_warning` | Valid policy has no fallback warning |
| `test_eval_does_not_affect_recommendations` | /recommendations/current unaffected |
| `test_eval_does_not_affect_overview` | /overview unaffected |
| `test_no_publication_from_eval` | No publication created |
| `test_existing_tests_pipeline_unchanged` | Pipeline still works |

---

## 4. Known Limitations

1. Adapter reset/step is not exposed via API endpoints yet (internal use only)
2. next_price lookups are per-asset per-day — can be slow for large exports
3. Policy evaluation still uses weekly step dates, not the full blend weight flexibility
4. No GPU, no neural nets, no external RL libraries

---

## 5. Recommended Next Phase

```
Phase 7C: FINRL-X Integration & Advanced Training
Do not start without explicit instruction.
```
