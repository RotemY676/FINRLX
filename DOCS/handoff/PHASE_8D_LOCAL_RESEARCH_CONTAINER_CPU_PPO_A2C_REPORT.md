# Phase 8D: Local Research Container for Real CPU PPO/A2C

**Date:** 2026-04-26
**Status:** Complete (Docker run NOT TESTED — no Docker daemon available; local PPO/A2C NOT TESTED — neural deps not installed on host)

---

## Executive Summary

Phase 8D creates a local-only, isolated research environment for running real CPU PPO/A2C experiments. Neural RL dependencies (torch, gymnasium, stable-baselines3) are installed only inside this isolated container/venv — the production Railway backend is completely unchanged.

The research container can:
1. Run real CPU PPO/A2C via stable-baselines3.
2. Consume the existing QuantPipeline offline dataset contract (or fall back to synthetic data).
3. Produce JSON research artifacts with full safety labeling.
4. Be run from PowerShell or Bash via Docker or local venv.
5. Keep production dependencies completely unchanged.

## Files Changed

```
NEW  research/finrlx_cpu/README.md                       — usage, safety, run instructions
NEW  research/finrlx_cpu/Dockerfile                       — local-only CPU research image
NEW  research/finrlx_cpu/requirements-research.txt        — neural deps (separate from production)
NEW  research/finrlx_cpu/train_cpu_rl.py                  — PPO/A2C trainer CLI
NEW  research/finrlx_cpu/env.py                           — Gymnasium-compatible offline portfolio env
NEW  research/finrlx_cpu/dataset_loader.py                — real JSON dataset loader + synthetic fallback
NEW  research/finrlx_cpu/artifact_schema.py               — artifact schema + validation
NEW  research/finrlx_cpu/export_artifact.py               — artifact JSON export
NEW  research/finrlx_cpu/sample_config.json               — sample training config
NEW  research/finrlx_cpu/scripts/run_research_container.ps1  — PowerShell Docker runner
NEW  research/finrlx_cpu/scripts/run_research_container.sh   — Bash Docker runner
NEW  research/finrlx_cpu/outputs/.gitkeep                 — output placeholder (gitignored)
NEW  research/finrlx_cpu/tests/test_artifact_schema.py    — 11 artifact schema tests
EDIT .gitignore                                           — exclude research outputs + .venv
NEW  DOCS/handoff/PHASE_8D_LOCAL_RESEARCH_CONTAINER_CPU_PPO_A2C_REPORT.md
```

No backend source files changed. No frontend files changed.

## Dependency Strategy

| File | Neural Deps | Used By |
|------|-------------|---------|
| `backend/requirements.txt` | **None** | Railway production |
| `research/finrlx_cpu/requirements-research.txt` | numpy, pandas, gymnasium, stable-baselines3, torch (CPU) | Local research only |

Production requirements are **unchanged**. Verified: `grep -i "torch\|gymnasium\|stable.baselines\|numpy" backend/requirements.txt` returns no matches.

## Confirmation: Production Requirements Unchanged

- `backend/requirements.txt`: NO torch, NO gymnasium, NO stable-baselines3, NO numpy.
- `backend/Dockerfile`: unchanged.
- `backend/railway.toml`: unchanged.
- `docker-compose.yml`: unchanged.
- Railway deploy path: unchanged.

## Local Research Container Design

### Dockerfile
- Base: `python:3.12-slim`
- Installs: numpy, pandas, gymnasium, stable-baselines3, torch (CPU-only via PyTorch CPU index)
- Labels: `purpose=finrlx-local-research-only`, `production=false`, `live_rl=false`, `broker_execution=false`
- Default CMD: runs a tiny PPO experiment

### Run scripts
- `scripts/run_research_container.ps1` — PowerShell, accepts -Algorithm, -Timesteps, -Seed params, mounts outputs volume
- `scripts/run_research_container.sh` — Bash, positional args (algorithm, timesteps, seed)

### Venv fallback (no Docker)
```
cd research/finrlx_cpu
python -m venv .venv
.venv/Scripts/activate  # or source .venv/bin/activate
pip install -r requirements-research.txt
python train_cpu_rl.py --algorithm PPO --timesteps 200 --seed 42
```

## Training Environment Design

`env.py` — `OfflinePortfolioEnv(gym.Env)`:
- **Actions** (Discrete 3): 0=neutral/cash (10% exposure), 1=baseline (80%), 2=risk-reduced (40%)
- **Observation** (Box 4): [engine_score, lagged_return, volatility_proxy, prev_action_encoded]
- **Reward**: realized_return * exposure - turnover_penalty (0.001 on action change)
- **Portfolio tracking**: cumulative value, peak tracking, max drawdown, turnover count
- **Dataset**: consumes rows with `engine_score` and `realized_return` fields
- **Fallback**: synthetic random data when no dataset row available

## Dataset Loader Behavior

`dataset_loader.py`:
- **Real dataset**: Loads JSON from file (flat list or `{"rows": [...]}` format). Flattens multi-asset rows to portfolio-level averages.
- **Synthetic fallback**: If no file provided or file not found, generates 60 deterministic synthetic rows with `rng = np.random.default_rng(seed)`.
- **Labeling**: Returns `(rows, synthetic_data: bool)` — synthetic is always explicitly labeled.

## Synthetic Data Fallback Behavior

When no dataset file is provided:
- `synthetic_data=True` in artifact
- Warning added: "Trained on SYNTHETIC data, not real market data."
- Data generated deterministically from seed
- Each row marked `synthetic: True`

Synthetic data is **never** silently presented as real.

## PPO/A2C Trainer Behavior

`train_cpu_rl.py`:
- CLI: `--algorithm PPO|A2C`, `--timesteps N`, `--seed N`, `--dataset path`, `--output-dir path`, `--save-model`
- Checks dependencies at import time; exits with clear message if missing
- Loads dataset (real or synthetic)
- Creates `OfflinePortfolioEnv`
- Trains via `stable_baselines3.PPO` or `.A2C` with `device="cpu"`
- Evaluates with deterministic policy
- Builds artifact via `artifact_schema.build_artifact()`
- Validates artifact via `artifact_schema.validate_artifact()`
- Saves to `outputs/artifact_{algo}_{timestamp}.json`
- Optionally saves SB3 model file (`.zip`)

## Artifact Schema

```json
{
  "artifact_type": "finrlx_cpu_rl_research_artifact",
  "schema_version": "1.0",
  "research_only": true,
  "offline_only": true,
  "shadow_only": true,
  "not_eligible_for_promotion": true,
  "live_pipeline_influence": false,
  "no_broker_execution": true,
  "no_publication_influence": true,
  "no_recommendation_pollution": true,
  "algorithm": "PPO",
  "real_neural_training": true,
  "cpu_only": true,
  "synthetic_data": true,
  "dataset_summary": { "row_count": 60, "synthetic": true },
  "training_config": { "algorithm": "PPO", "timesteps": 200, "seed": 42, "device": "cpu" },
  "training_metrics": { "total_reward": 0.012, "final_portfolio_value": 1.012, "max_drawdown": 0.005, "training_duration_ms": 1234 },
  "artifact_created_at": "2026-04-26T12:00:00Z",
  "warnings": ["Local CPU research artifact only.", "Not eligible for promotion.", ...]
}
```

## Run Instructions

### Docker (recommended)
```powershell
cd C:\Users\Rotem\projects\FINRLX\research\finrlx_cpu\scripts
.\run_research_container.ps1 -Algorithm PPO -Timesteps 200 -Seed 42
# Artifacts saved to research/finrlx_cpu/outputs/
```

### Local venv
```powershell
cd C:\Users\Rotem\projects\FINRLX\research\finrlx_cpu
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-research.txt
python train_cpu_rl.py --algorithm PPO --timesteps 200 --seed 42
```

### With real dataset
```powershell
python train_cpu_rl.py --algorithm A2C --timesteps 500 --seed 7 --dataset exported_data.json
```

## Test Results

### Research artifact schema tests (11 tests)
```
11 passed in 0.09s
```
These tests do NOT require neural dependencies.

### Backend regression tests
```
375 passed, 2 skipped — zero regressions
```
Production Phase 8C behavior unchanged.

## Backend Regression Result

- All 375 backend tests pass.
- `/rl/finrlx/train-cpu-prototype` still returns `dependency_unavailable` when deps absent.
- `/rl/execute` remains 404.
- Benchmark regression works.
- No production dependencies changed.

## Whether Real PPO/A2C Was Run Locally

**NOT TESTED** — neural dependencies (torch, gymnasium, stable-baselines3) are not installed on the development host. The trainer script, environment, and artifact schema are implemented and structurally validated. Real execution requires either Docker or a local venv with research dependencies installed.

## Whether Docker Run Was Tested

**NOT TESTED** — Docker daemon was not available during this session. The Dockerfile, run scripts, and mount configuration are implemented but not executed.

## Safety Model

All research artifacts include mandatory safety flags enforced by `artifact_schema.py`:

| Flag | Value | Meaning |
|------|-------|---------|
| `research_only` | true | Not production |
| `offline_only` | true | No live data |
| `shadow_only` | true | No live influence |
| `not_eligible_for_promotion` | true | Cannot become production policy |
| `live_pipeline_influence` | false | No pipeline impact |
| `no_broker_execution` | true | No orders |
| `no_publication_influence` | true | No publication impact |
| `no_recommendation_pollution` | true | No recommendation impact |

`validate_artifact()` rejects any artifact missing these flags or with wrong values.

## Known Limitations

1. Docker/venv not tested in this session (deps not installed on host).
2. Discrete 3-action space is a simplification of real portfolio allocation.
3. Reward function is basic; real portfolio optimization needs more sophisticated shaping.
4. Synthetic data does not capture real market microstructure.
5. No automatic import back to backend (deferred to Phase 8E).
6. CPU training is slower than GPU but sufficient for small research experiments.
7. `export_training_dataset` backend endpoint must be called manually to get real data.

## Stop/Go Recommendation for Phase 8E

**GO** — with conditions:

Phase 8E should connect local research artifacts back into the backend as shadow-only research candidates. Requirements:

1. **Artifact import endpoint**: `POST /api/v1/rl/finrlx/import-research-artifact` accepting the artifact JSON.
2. **Validation**: Must validate artifact schema including all safety flags before import.
3. **Candidate creation**: Create `RLPolicySnapshot` with `policy_type=finrlx_cpu_{algo}_research_import`.
4. **Isolation**: Imported candidates must pass the same `get_candidate_isolation()` checks (all blocked).
5. **Benchmark integration**: Imported artifacts should be benchmarkable via existing `POST /api/v1/rl/benchmarks/run`.
6. **No promotion path**: Phase 8E must NOT add any promotion/publication capability.
7. **Audit trail**: Import must create audit events with full artifact provenance.

The existing benchmark layer (`rl_benchmark.py`) and candidate isolation system are ready to support imported artifacts. The artifact schema includes enough metadata for audit provenance.

## Design Handoff Review

**Files reviewed:**
- `design/handoff-package/HANDOFF.md` — full 32KB spec, 14 web surfaces, component catalog
- `design/handoff-package/Ops.html` — ops status pills, audit timeline, incident panels
- `design/handoff-package/Backtests.html` — equity curves, tear sheets, research run patterns
- `design/handoff-package/styles.css` + `tokens.css` — OKLCH tokens, semantic colors, density modes
- `design/handoff-package/ops.css` + `backtests.css` — specific component styles

**UI touched:** No. Phase 8D is entirely research infrastructure (Dockerfile, Python scripts, artifact schema). No frontend or admin page changes.

**Why design was still reviewed:** To confirm that if future phases (8E) add UI for artifact import/review, the existing ops status pills, backtests tear-sheet patterns, and audit timeline patterns are ready to be reused. No new design system needed.

## Safety Confirmations

| Check | Status |
|-------|--------|
| No live RL added | CONFIRMED |
| No broker execution | CONFIRMED |
| No auto-trading | CONFIRMED |
| No recommendation pollution | CONFIRMED |
| No overview pollution | CONFIRMED |
| No publication influence | CONFIRMED |
| No production dependency changes | CONFIRMED |
| All artifacts research/offline/shadow only | CONFIRMED |
| Production requirements unchanged | CONFIRMED |
| Railway deploy path unchanged | CONFIRMED |
| Backend tests pass (375+11=386 total) | CONFIRMED |

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Local research folder exists | PASS |
| 2 | Local Dockerfile exists | PASS |
| 3 | Research requirements separate from production | PASS |
| 4 | Production requirements have no neural deps | PASS |
| 5 | PowerShell run script exists | PASS |
| 6 | README explains usage and safety | PASS |
| 7 | Gymnasium-compatible environment exists | PASS |
| 8 | PPO/A2C trainer script exists | PASS |
| 9 | Trainer can run locally if deps available | PASS (structurally; NOT TESTED with real deps) |
| 10 | NOT TESTED clearly stated | PASS |
| 11 | Artifact schema has all safety flags | PASS |
| 12 | Synthetic data labeled honestly | PASS |
| 13 | Outputs in local research folder only | PASS |
| 14 | Generated outputs gitignored | PASS |
| 15 | No production API/DB touched by default | PASS |
| 16 | Backend tests pass | PASS (375 passed) |
| 17 | Production Phase 8C behavior unchanged | PASS |
| 18 | /rl/execute remains unavailable | PASS |
| 19 | Benchmark regression works | PASS |
| 20 | Design handoff reviewed and documented | PASS |
| 21 | Run instructions in report | PASS |
| 22 | Stop/Go for Phase 8E included | PASS (GO with conditions) |
| 23 | No live RL/broker/recommendation/overview/publication | PASS |
| 24 | No production dependency path changed | PASS |
