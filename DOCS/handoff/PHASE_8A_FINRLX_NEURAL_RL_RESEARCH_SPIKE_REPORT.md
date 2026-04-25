# Phase 8A: FinRL-X Neural RL Research Spike — Report

**Date:** 2026-04-25
**Phase:** 8A — Offline research feasibility spike
**Status:** Complete

**Real FinRL-X training was NOT implemented in Phase 8A.**

---

## 1. Executive Summary

Phase 8A implements a strictly isolated FinRL-X research adapter with dataset contract validation, a stubbed training interface, shadow-only policy candidate export, and safety guards. No ML/RL libraries are installed — this is an honest interface stub that validates the integration contract and documents exact dependencies needed for real neural training.

---

## 2. Files Changed

### Backend (3 created, 1 modified)
```
backend/app/services/finrlx_research.py    — FinRLXResearchService (adapter, validation, stub trainer, candidate export, safety guard)
backend/app/api/v1/rl_finrlx.py            — 5 research endpoints
backend/tests/test_phase8a_finrlx_research.py — 13 tests
backend/app/api/router.py                  — registered rl_finrlx_router
```

### Frontend (2 modified)
```
frontend/src/services/api.ts               — FinRLXAdapterStatus type + fetchFinRLXStatus()
frontend/src/app/admin/page.tsx            — FinRL-X Research Spike panel
```

### Documentation (1 created)
```
DOCS/handoff/PHASE_8A_FINRLX_NEURAL_RL_RESEARCH_SPIKE_REPORT.md
```

---

## 3. API Endpoints Added (5)

| Method | Path | Purpose |
|---|---|---|
| GET | `/rl/finrlx/status` | Adapter info + dependency status |
| POST | `/rl/finrlx/validate-dataset` | Validate dataset contract |
| POST | `/rl/finrlx/train-research` | Run stubbed research training (requires research_acknowledgement=true) |
| GET | `/rl/finrlx/candidates` | List research candidates |
| GET | `/rl/finrlx/candidates/{id}` | Single candidate detail |

---

## 4. RL Architecture Reviewed

- **Environment:** `quantpipeline_offline_v1` with state/action/reward
- **Adapter:** Gym-like reset/step interface
- **Agents:** 3 baseline (heuristic, random, score_weighted)
- **Training:** Deterministic grid search producing policy snapshots
- **Benchmarks:** Multi-agent comparison with audit trail, fingerprints, invariants
- **Dataset export:** Daily rows with ticker/price/next_price/realized_return/engine_score

---

## 5. Dataset Contract Assessment

Current export provides:
- `as_of_date`, `next_date`, `universe_tickers`, `policy_constraints`
- Per-asset: `ticker`, `price`, `next_price`, `realized_return`, `engine_score`

**Valid for FinRL-X:** Yes — covers required OHLCV proxy (close prices), forward returns, and feature signals.
**Gaps:** No open/high/low/volume (only close), no intraday, 90 days only, 10 assets.

---

## 6. FinRL-X Dependency Assessment

**Installed ML libraries:** None.
**Missing for real training:**
- numpy
- torch or tensorflow
- gymnasium or gym
- stable-baselines3 or finrl
- pandas

**GPU required:** No (can start CPU-only)
**Production runtime dependency:** None (research isolated)

---

## 7. Training Implementation: STUBBED

The `train_research_stub()` method:
- Validates dataset contract
- Creates a RLTrainingRun with `config.training_mode="stubbed"` and `config.real_neural_training=False`
- Creates a RLPolicySnapshot with `policy_type="finrlx_research_stub"` and explicit safety flags
- Returns warnings: "Real FinRL-X training was NOT performed", "No ML/RL libraries are installed"

No real neural computation occurs. The stub validates the interface contract only.

---

## 8. Safety Model

**Safety guard blocks:** mark_as_live, publish, execute, promote, affect_recommendations, affect_overview, affect_publication, broker_execution

**Every response includes:**
- research_only=true, offline_only=true, shadow_only=true
- live_pipeline_influence=false, no_broker_execution=true
- no_publication_influence=true, no_recommendation_pollution=true

**Train endpoint requires:** `research_acknowledgement=true` (422 if missing)

---

## 9. Design Handoff Review

**Files reviewed:** `HANDOFF.md`, `tokens.css`, `styles.css`, `Ops.html`, `Design System.html`
**Patterns reused:** Card layout, badge styling (`bg-surface-3 text-ink-3`), grid metrics, caution warning panel, `text-accent-2` for research icon.
**No new UI style introduced.**

---

## 10. Tests

**Backend:** 331 passed, 2 skipped — 13 new Phase 8A tests, zero regressions
**Frontend:** Compiled, types checked, 11/11 pages. `/admin` = 12.1 kB.

---

## 11. Production Smoke Commands

```powershell
$base = "https://backend-production-aab8.up.railway.app/api/v1"

Invoke-RestMethod "$base/health"
Invoke-RestMethod "$base/rl/finrlx/status"

Invoke-RestMethod "$base/rl/finrlx/validate-dataset" -Method POST -ContentType "application/json" -Body '{"limit":5}'

$train = Invoke-RestMethod "$base/rl/finrlx/train-research" -Method POST -ContentType "application/json" -Body '{"research_acknowledgement":true}'
$train.data.training_mode
$train.data.real_neural_training
$train.data.safety_flags | ConvertTo-Json -Depth 5

Invoke-RestMethod "$base/rl/finrlx/candidates"

try { Invoke-RestMethod "$base/rl/execute" -Method POST -ContentType "application/json" -Body "{}" } catch { $_.Exception.Response.StatusCode.value__ }
Invoke-RestMethod "$base/overview"
Invoke-RestMethod "$base/recommendations/current"

$b = Invoke-RestMethod "$base/rl/benchmarks/run" -Method POST -ContentType "application/json" -Body '{"start_date":"2026-03-15","end_date":"2026-04-15"}'
$b.data.status
```

---

## 12. Known Limitations

1. No real neural training — stubbed interface only
2. No ML/RL libraries installed
3. No GPU support
4. Dataset is 90 days, 10 assets — insufficient for real RL
5. No model weight persistence (stub weights are hardcoded)
6. No FinRL-X framework integration

---

## 13. Stop/Go Recommendation for Phase 8B

**GO — with conditions:**

The dataset contract, adapter interface, benchmark layer, and audit trail are ready. To proceed to Phase 8B (real neural training):

1. Install: `numpy`, `torch` (CPU), `gymnasium`, `stable-baselines3`
2. Extend dataset to ≥1 year of daily bars
3. Implement PPO/A2C agent using stable-baselines3 with the existing Gym-like adapter
4. Keep all training offline/shadow-only
5. Evaluate trained policies through existing benchmark layer

**Do not start Phase 8B without explicit instruction.**

---

## 14. Safety Confirmations

- **No live RL** — CONFIRMED
- **No broker execution** — CONFIRMED
- **No auto-trading** — CONFIRMED
- **No recommendation pollution** — CONFIRMED
- **No overview pollution** — CONFIRMED
- **No publication influence** — CONFIRMED
- **All FinRL-X outputs are research/offline/shadow only** — CONFIRMED
- **Real FinRL-X training was NOT implemented** — CONFIRMED
- **design/handoff-package reviewed** — CONFIRMED
