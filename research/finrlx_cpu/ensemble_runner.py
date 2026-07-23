#!/usr/bin/env python3
"""LEAP A3 (D45) — FinRL ensemble runner for the E7 research worker.

Trains the ICAIF-2020 ensemble (PPO / A2C / DDPG via stable-baselines3) on a
single ticker's daily bars inside the isolated research environment, scores
every agent on the SAME walk-forward splits the production service uses, and
publishes the E.6 artifact that `app.services.finrl_ensemble` merges into the
tournament.

Usage (on the worker, torch + stable-baselines3 installed):
    python ensemble_runner.py --ticker NVDA \
        --states-json /path/exported_states.json \
        --out ../artifacts/finrl_ensemble/NVDA.json

`states-json` is exported by the backend (`scripts/export_states.py`, same
rebalance/state pipeline), so the reward windows are byte-identical to what
local candidates were scored on — the protocol-match gate depends on it.

This file is import-safe without torch (guards below) so the backend test
suite can lint it; actual training only runs where E7 provides the stack.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys
from datetime import UTC, datetime

SCHEMA_VERSION = "e6-1"
RECIPE = "icaif2020-ensemble"
AGENTS = ("rl_ppo", "rl_a2c", "rl_ddpg")
TURBULENCE_LIQUIDATE_PCTL = 0.99  # ICAIF recipe: extreme-regime circuit breaker


def _require_stack():
    try:
        import stable_baselines3  # noqa: F401
        import torch  # noqa: F401
    except ImportError as exc:  # pragma: no cover — worker-only path
        sys.exit(
            f"research stack missing ({exc}); this runner is E7-worker-only. "
            "The backend degrades honestly without artifacts."
        )


def sharpe(returns: list[float]) -> float:
    n = len(returns)
    if n < 2:
        return 0.0
    mean = math.fsum(returns) / n
    var = math.fsum((r - mean) ** 2 for r in returns) / (n - 1)
    # Constant/near-constant series have no meaningful Sharpe. The epsilon is
    # relative to the mean's scale so float-summation residue (which differs
    # across Python versions: 3.12 sum() is compensated, 3.11 is not) can
    # never masquerade as real variance and explode the ratio.
    if var <= (1e-9 * max(abs(mean), 1e-12)) ** 2:
        return 0.0
    return (mean / math.sqrt(var)) * math.sqrt(52)


def train_and_score(states: list[dict], splits: list[list[int]]) -> dict:  # pragma: no cover
    """Worker-only: train each agent per split's train window, evaluate on the
    validation window via the shared TradingEnv, return E.6 agent blocks."""
    _require_stack()
    from stable_baselines3 import A2C, DDPG, PPO

    # The environment is OfflinePortfolioEnv. This module imported `TradingEnv`
    # — a name that exists nowhere in the repository — so `train_and_score` had
    # never executed: it raised ImportError on the first call, which is why
    # `research/artifacts/` was never created and the Desk's RL leg reported
    # "queued for research run" indefinitely. The queue had no worker attached.
    from env import OfflinePortfolioEnv

    algos = {"rl_ppo": PPO, "rl_a2c": A2C, "rl_ddpg": DDPG}
    out: dict[str, dict] = {}
    for key, Algo in algos.items():
        per_split_val, per_split_train = [], []
        for train_end, val_end in splits:
            env = OfflinePortfolioEnv(states[:train_end])
            model = Algo("MlpPolicy", env, verbose=0, seed=1337)
            model.learn(total_timesteps=20_000)
            per_split_train.append(sharpe(env.episode_returns()))
            val_env = OfflinePortfolioEnv(states[train_end:val_end])
            obs, _ = val_env.reset()
            done = False
            while not done:
                action, _ = model.predict(obs, deterministic=True)
                obs, _, done, _, _ = val_env.step(action)
            # Fail closed: the env pads short windows from a synthetic
            # generator. A Sharpe computed over invented rows is not evidence
            # and must not reach the tournament as a competing candidate.
            if val_env.used_synthetic() or env.used_synthetic():
                raise ValueError(
                    f"{key}: episode fell back to synthetic rows for split "
                    f"({train_end},{val_end}) — refusing to score it. Export a "
                    "longer real state series before running the ensemble."
                )
            per_split_val.append(sharpe(val_env.episode_returns()))
        out[key] = {
            "name": f"{key.split('_')[1].upper()} (FinRL ensemble)",
            "train_sharpe": round(sum(per_split_train) / len(per_split_train), 4),
            "val_sharpe": round(sum(per_split_val) / len(per_split_val), 4),
            "per_split_val_sharpe": [round(v, 4) for v in per_split_val],
        }
    return out


def quarterly_selection(agents: dict, splits: list[list[int]]) -> list[dict]:
    """ICAIF selection: per validation block, the agent with the best block
    Sharpe 'drives' — surfaced as the selection-history strip."""
    history = []
    for i, (_, _) in enumerate(splits):
        best_key, best_v = None, -1e9
        for key, a in agents.items():
            v = a["per_split_val_sharpe"][i]
            if v > best_v:
                best_key, best_v = key, v
        history.append({
            "period": f"split-{i + 1}",
            "selected": best_key,
            "val_sharpe": round(best_v, 4),
            "turbulence_gate": False,  # gate events computed from states below
        })
    return history


def main() -> None:  # pragma: no cover — worker entrypoint
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--states-json", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    payload = json.loads(pathlib.Path(args.states_json).read_text())
    states, splits = payload["states"], payload["splits"]
    agents = train_and_score(states, splits)
    artifact = {
        "schema_version": SCHEMA_VERSION,
        "ticker": args.ticker.upper(),
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "recipe": RECIPE,
        "splits": splits,
        "agents": agents,
        "selection_history": quarterly_selection(agents, splits),
        "turbulence_events": payload.get("turbulence_events", []),
    }
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, indent=2))
    print(f"artifact written: {out}")


if __name__ == "__main__":  # pragma: no cover
    main()
