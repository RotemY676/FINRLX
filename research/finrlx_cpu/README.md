# FinRL-X CPU-only Local Research Container

## What this is

A **local-only** research environment for running real CPU PPO/A2C experiments using the FinRL-X/QuantPipeline offline dataset contract. It installs neural RL dependencies (torch, gymnasium, stable-baselines3) in an isolated container or venv, completely separate from the production Railway backend.

## What this is NOT

- **Not a production system.** This does not run on Railway.
- **Not live RL.** No broker execution, no order placement, no auto-trading.
- **Not connected to production.** Does not access the production database or API by default.
- **Not eligible for promotion.** Research artifacts cannot be promoted to production policies.
- **Not used by live recommendations.** No influence on `/recommendations/current`, `/overview`, or publication workflow.

## Safety restrictions

All outputs are labeled:
- `research_only: true`
- `offline_only: true`
- `shadow_only: true`
- `not_eligible_for_promotion: true`
- `no_broker_execution: true`
- `no_publication_influence: true`
- `no_recommendation_pollution: true`
- `live_pipeline_influence: false`

## How to run

### Option 1: Docker (recommended)

```powershell
# PowerShell
cd research/finrlx_cpu/scripts
.\run_research_container.ps1 -Algorithm PPO -Timesteps 200 -Seed 42
```

```bash
# Bash / WSL
cd research/finrlx_cpu/scripts
chmod +x run_research_container.sh
./run_research_container.sh PPO 200 42
```

### Option 2: Local venv (no Docker)

```powershell
cd research/finrlx_cpu
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-research.txt
python train_cpu_rl.py --algorithm PPO --timesteps 200 --seed 42
```

### With a real dataset export

```powershell
# First export dataset from the backend (local dev only):
# curl -X POST http://localhost:8000/api/v1/rl/training/export-dataset \
#   -H 'Content-Type: application/json' \
#   -d '{"start_date":"2026-03-01","end_date":"2026-04-15"}' > dataset.json

python train_cpu_rl.py --algorithm PPO --timesteps 500 --dataset dataset.json
```

### Save the trained model

```powershell
python train_cpu_rl.py --algorithm PPO --timesteps 500 --seed 42 --save-model
```

## Expected output

The trainer produces a JSON research artifact in `outputs/`:

```json
{
  "artifact_type": "finrlx_cpu_rl_research_artifact",
  "algorithm": "PPO",
  "real_neural_training": true,
  "cpu_only": true,
  "synthetic_data": true,
  "training_metrics": {
    "total_reward": 0.012345,
    "final_portfolio_value": 1.0123,
    "max_drawdown": 0.005,
    "training_duration_ms": 1234
  },
  "research_only": true,
  "not_eligible_for_promotion": true,
  "no_broker_execution": true
}
```

## How to delete outputs

```powershell
# Remove all generated artifacts and models
Remove-Item -Recurse -Force research/finrlx_cpu/outputs/*
# Keep the .gitkeep
New-Item research/finrlx_cpu/outputs/.gitkeep -ItemType File -Force
```

## Known limitations

- Discrete 3-action space (cash/baseline/risk-reduced) is a simplification.
- Reward function is basic (return * exposure - turnover penalty).
- Synthetic data does not capture real market dynamics.
- CPU training is slower than GPU but sufficient for small experiments.
- No automatic import back into the backend (deferred to Phase 8E).

## No production influence statement

This research container has **zero connection** to production systems. It does not:
- Read from or write to the production database
- Call production API endpoints
- Influence live recommendations, publication, or overview
- Execute broker orders or trades
- Promote policies or replace baseline agents

All artifacts produced are research-only and must be manually validated before any future integration (Phase 8E).
