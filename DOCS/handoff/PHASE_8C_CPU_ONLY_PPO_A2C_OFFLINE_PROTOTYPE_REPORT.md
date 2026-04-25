# Phase 8C: CPU-only PPO/A2C Offline Prototype — Report

**Date:** 2026-04-25
**Phase:** 8C — CPU-only neural RL prototype with graceful fallback
**Status:** Complete

---

## 1. Executive Summary

Phase 8C implements a CPU-only PPO/A2C research prototype with graceful dependency detection. When numpy/gymnasium/stable-baselines3/torch are available, it runs a real tiny offline training job. When dependencies are missing (current production state), it falls back truthfully to `dependency_unavailable` status and creates an honest stub candidate. All outputs remain research/offline/shadow only with full isolation, audit, and fingerprint support.

---

## 2. Dependencies

**torch/gymnasium/stable-baselines3 were NOT installed.** Adding torch (~2GB) to production requirements.txt would break Railway deploy. All imports are lazy/optional. The app boots and functions normally without them.

**Dependency status (production):**
- numpy: missing
- gymnasium: missing
- stable_baselines3: missing
- torch: missing
- neural_training_available: false
- cpu_only_mode: true

---

## 3. Whether Real CPU PPO/A2C Ran

**NO.** Dependencies are not installed in production. The prototype correctly returns `status="dependency_unavailable"` and `real_neural_training=false`. The code path for real training exists and will activate when dependencies are installed locally.

---

## 4. Files Changed

### Backend (2 modified, 1 created)
```
backend/app/services/finrlx_research.py    — get_neural_dependency_status(), train_cpu_prototype(), _build_component_checks()
backend/app/api/v1/rl_finrlx.py            — GET /dependencies, POST /train-cpu-prototype endpoints
backend/tests/test_phase8c_cpu_prototype.py — 16 tests
```

### Frontend (2 modified)
```
frontend/src/services/api.ts               — FinRLXDependencyStatus type, fetchFinRLXDependencies()
frontend/src/app/admin/page.tsx            — CPU-only dependency status section in FinRL-X panel
```

### Documentation (1 created)
```
DOCS/handoff/PHASE_8C_CPU_ONLY_PPO_A2C_OFFLINE_PROTOTYPE_REPORT.md
```

---

## 5. API Endpoints Added (2)

| Method | Path | Purpose |
|---|---|---|
| GET | `/rl/finrlx/dependencies` | Neural dependency status |
| POST | `/rl/finrlx/train-cpu-prototype` | Run CPU-only PPO/A2C prototype or return dependency_unavailable |

---

## 6. Training Configuration

- `algorithm`: PPO or A2C (validated)
- `timesteps`: 1-500 (capped, rejected above 500)
- `seed`: deterministic
- `research_acknowledgement`: required (422 if missing)
- CPU-only mode enforced
- No GPU required

---

## 7. Candidate Behavior

When dependencies unavailable:
- `status: "dependency_unavailable"`, `training_mode: "dependency_unavailable"`, `real_neural_training: false`
- Candidate created with `policy_type: "finrlx_cpu_ppo_unavailable"` (or a2c)
- `not_eligible_for_promotion: true`

When dependencies available (local dev with torch installed):
- `status: "completed"`, `training_mode: "cpu_ppo"`, `real_neural_training: true`
- Tiny Gymnasium env with discrete action space (cash/baseline/risk-reduced)
- stable-baselines3 PPO/A2C with MlpPolicy, CPU device
- Training metrics: timesteps, duration_ms, final_mean_reward, seed

---

## 8. Design Handoff Review

**Files reviewed:** `HANDOFF.md`, `tokens.css`, `styles.css`, `Ops.html`, `Design System.html`
**Patterns reused:** Dependency badges (`bg-pos-soft`/`bg-surface-3`), card layout, section divider.
**No new UI style introduced.**

---

## 9. Tests

**Backend:** 361 passed, 2 skipped — 16 new, zero regressions
**Frontend:** Compiled, types checked, 11/11 pages.

---

## 10. Production Smoke Commands

```powershell
$base = "https://backend-production-aab8.up.railway.app/api/v1"

Invoke-RestMethod "$base/health"
Invoke-RestMethod "$base/rl/finrlx/dependencies"

$r = Invoke-RestMethod "$base/rl/finrlx/train-cpu-prototype" -Method POST -ContentType "application/json" -Body '{"algorithm":"PPO","timesteps":50,"research_acknowledgement":true}'
$r.data.status
$r.data.training_mode
$r.data.real_neural_training
$r.data.safety_flags | ConvertTo-Json -Depth 5

try { Invoke-RestMethod "$base/rl/execute" -Method POST -ContentType "application/json" -Body "{}" } catch { $_.Exception.Response.StatusCode.value__ }
Invoke-RestMethod "$base/overview"
Invoke-RestMethod "$base/recommendations/current"
```

---

## 11. Known Limitations

1. No real neural training in production — dependencies not installed
2. torch (~2GB) too large for Railway free tier
3. Tiny synthetic environment (discrete 3-action) — not representative of real portfolio optimization
4. No model weight serialization — candidate stores metadata only
5. Cannot evaluate CPU prototype candidate through existing benchmark layer (different action space)

---

## 12. Stop/Go for Phase 8D

**CONDITIONAL GO:**
- Install numpy+torch(CPU)+gymnasium+stable-baselines3 in a local/dev environment
- Run the CPU prototype locally to verify real training path
- Consider a separate research container for neural training (not Railway production)
- Phase 8D should focus on continuous action space + proper portfolio env + benchmark integration

**Do not start Phase 8D without explicit instruction.**

---

## 13. Safety Confirmations

- **No live RL** — CONFIRMED
- **No broker execution** — CONFIRMED
- **No auto-trading** — CONFIRMED
- **No recommendation pollution** — CONFIRMED
- **No overview pollution** — CONFIRMED
- **No publication influence** — CONFIRMED
- **All outputs research/offline/shadow only** — CONFIRMED
- **No torch/gymnasium/stable-baselines3 installed in production** — CONFIRMED
- **Candidate not eligible for promotion** — CONFIRMED
- **design/handoff-package reviewed** — CONFIRMED
