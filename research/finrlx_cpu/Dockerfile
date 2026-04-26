# ============================================================
# FinRL-X CPU-only Research Container
# ============================================================
# LOCAL RESEARCH ONLY — not used by Railway production.
# This image installs neural RL dependencies (torch, gymnasium,
# stable-baselines3) for offline CPU PPO/A2C experiments.
#
# No broker execution, no live RL, no production influence.
# ============================================================

FROM python:3.12-slim

LABEL purpose="finrlx-local-research-only"
LABEL production="false"
LABEL live_rl="false"
LABEL broker_execution="false"

WORKDIR /research

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install research-only Python dependencies (CPU torch)
COPY requirements-research.txt .
RUN pip install --no-cache-dir -r requirements-research.txt

# Copy research code
COPY . .

# Default: run a tiny PPO experiment
CMD ["python", "train_cpu_rl.py", "--algorithm", "PPO", "--timesteps", "200", "--seed", "42"]
