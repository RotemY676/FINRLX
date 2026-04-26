"""FinRL-X CPU-only PPO/A2C research trainer.

LOCAL RESEARCH ONLY — not used by Railway production.
No broker execution. No live RL. No production influence.
All outputs are research-only, offline-only, shadow-only.
Not eligible for promotion. Not used by production decisions.

Usage:
    python train_cpu_rl.py --algorithm PPO --timesteps 200 --seed 42
    python train_cpu_rl.py --algorithm A2C --timesteps 500 --seed 7 --dataset data.json
    python train_cpu_rl.py --algorithm PPO --timesteps 200 --output-dir ./outputs
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── Dependency check ────────────────────────────────────────────────────

MISSING_DEPS = []
try:
    import numpy as np
except ImportError:
    MISSING_DEPS.append("numpy")

try:
    import gymnasium as gym
except ImportError:
    MISSING_DEPS.append("gymnasium")

try:
    from stable_baselines3 import PPO, A2C
except ImportError:
    MISSING_DEPS.append("stable-baselines3")

try:
    import torch
except ImportError:
    MISSING_DEPS.append("torch")


def main():
    parser = argparse.ArgumentParser(
        description="FinRL-X CPU-only PPO/A2C research trainer (local only)",
    )
    parser.add_argument("--algorithm", choices=["PPO", "A2C"], default="PPO")
    parser.add_argument("--timesteps", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dataset", type=str, default=None, help="Path to dataset JSON")
    parser.add_argument("--output-dir", type=str, default="outputs")
    parser.add_argument("--save-model", action="store_true", help="Save SB3 model file")
    args = parser.parse_args()

    print("=" * 60)
    print("FinRL-X CPU-only Research Trainer")
    print("LOCAL RESEARCH ONLY — no production influence")
    print("=" * 60)

    if MISSING_DEPS:
        print(f"\nMissing dependencies: {', '.join(MISSING_DEPS)}")
        print("Install via: pip install -r requirements-research.txt")
        print("Or run in Docker: see scripts/run_research_container.ps1")
        sys.exit(1)

    # Import local modules (only after dep check)
    from dataset_loader import load_dataset
    from env import OfflinePortfolioEnv
    from artifact_schema import build_artifact, validate_artifact
    from export_artifact import save_artifact

    # Load dataset
    print(f"\nDataset: {args.dataset or '(synthetic fallback)'}")
    rows, synthetic = load_dataset(args.dataset, seed=args.seed)
    print(f"  Rows: {len(rows)}, Synthetic: {synthetic}")

    # Create environment
    env = OfflinePortfolioEnv(dataset=rows, seed=args.seed)

    # Train
    print(f"\nTraining {args.algorithm} for {args.timesteps} timesteps (CPU, seed={args.seed})...")
    algo_cls = PPO if args.algorithm == "PPO" else A2C
    t0 = time.monotonic()
    model = algo_cls(
        "MlpPolicy", env, verbose=0, seed=args.seed, device="cpu",
    )
    model.learn(total_timesteps=args.timesteps)
    training_ms = int((time.monotonic() - t0) * 1000)
    print(f"  Training completed in {training_ms}ms")

    # Evaluate
    obs, _ = env.reset(seed=args.seed + 1)
    done = False
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, done, truncated, info = env.step(int(action))
        if truncated:
            break

    metrics = env.get_metrics()
    print(f"\nEvaluation metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    # Build artifact
    now = datetime.now(timezone.utc).isoformat()
    warnings = [
        "Local CPU research artifact only.",
        "Not eligible for promotion.",
        "Not used by production decisions.",
        "No broker execution.",
    ]
    if synthetic:
        warnings.append("Trained on SYNTHETIC data, not real market data.")

    artifact = build_artifact(
        algorithm=args.algorithm,
        real_neural_training=True,
        synthetic_data=synthetic,
        dataset_summary={
            "row_count": len(rows),
            "synthetic": synthetic,
            "source": args.dataset or "synthetic_fallback",
        },
        training_config={
            "algorithm": args.algorithm,
            "timesteps": args.timesteps,
            "seed": args.seed,
            "device": "cpu",
            "policy": "MlpPolicy",
        },
        training_metrics={
            **metrics,
            "training_duration_ms": training_ms,
        },
        created_at=now,
        warnings=warnings,
    )

    # Validate
    valid, errors = validate_artifact(artifact)
    if not valid:
        print(f"\nArtifact validation FAILED: {errors}")
        sys.exit(1)

    # Save
    output_dir = args.output_dir
    artifact_path = save_artifact(artifact, output_dir)
    print(f"\nArtifact saved: {artifact_path}")

    # Optionally save model
    if args.save_model:
        model_path = Path(output_dir) / f"model_{args.algorithm.lower()}_{args.seed}.zip"
        model.save(str(model_path))
        print(f"Model saved: {model_path}")

    print("\n" + "=" * 60)
    print("Research training complete.")
    print("This artifact is LOCAL RESEARCH ONLY.")
    print("Not eligible for promotion. No production influence.")
    print("=" * 60)

    return artifact


if __name__ == "__main__":
    main()
