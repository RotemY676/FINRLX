#!/usr/bin/env bash
# ============================================================
# FinRL-X CPU-only Research Container — Bash
# ============================================================
# LOCAL RESEARCH ONLY — not used by Railway production.
# No broker execution. No live RL. No production influence.
# ============================================================

set -euo pipefail

ALGORITHM="${1:-PPO}"
TIMESTEPS="${2:-200}"
SEED="${3:-42}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RESEARCH_DIR="$(dirname "$SCRIPT_DIR")"
IMAGE_NAME="finrlx-cpu-research"

echo "============================================================"
echo "FinRL-X CPU-only Research Container"
echo "LOCAL RESEARCH ONLY — no production influence"
echo "============================================================"
echo ""

# Build
echo "Building research image..."
docker build -t "$IMAGE_NAME" "$RESEARCH_DIR"

# Run
mkdir -p "$RESEARCH_DIR/outputs"

echo "Running: PPO=$ALGORITHM timesteps=$TIMESTEPS seed=$SEED"
echo ""

docker run --rm \
    -v "$RESEARCH_DIR/outputs:/research/outputs" \
    "$IMAGE_NAME" \
    python train_cpu_rl.py \
        --algorithm "$ALGORITHM" \
        --timesteps "$TIMESTEPS" \
        --seed "$SEED" \
        --output-dir /research/outputs

echo ""
echo "Research complete. Artifacts in: $RESEARCH_DIR/outputs/"
echo "These artifacts are LOCAL RESEARCH ONLY."
