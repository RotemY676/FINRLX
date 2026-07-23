"""The RL ensemble producer can actually start.

Review finding 2026-07-23: `research/finrlx_cpu/ensemble_runner.py` imported
`TradingEnv`, a class that exists nowhere in the repository — the environment
is `OfflinePortfolioEnv`. `train_and_score` therefore raised ImportError on its
first call and had never run once. That is why `research/artifacts/` was never
created, why `finrl_ensemble.load_artifact()` always returned None, and why the
Desk's RL panel reported "queued for research run" permanently: the queue had
no worker attached to it.

These tests cover the contract the runner depends on WITHOUT requiring torch or
stable-baselines3, which are deliberately not backend dependencies. They pin
the env API and the fail-closed synthetic guard; producing a real artifact
still requires the research container (operator item E7).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

RESEARCH = Path(__file__).resolve().parents[2] / "research" / "finrlx_cpu"

# Only the tests that INSTANTIATE the env need gymnasium. The import-integrity
# test below is pure text analysis and must always run — it is the one that
# catches the defect that kept the producer dead, and skipping it wherever the
# research stack is absent (i.e. everywhere the backend runs) would mean it
# never runs at all.
needs_gym = pytest.mark.skipif(
    importlib.util.find_spec("gymnasium") is None,
    reason="research env needs gymnasium (deliberately not a backend dep)",
)


def _load_env_module():
    spec = importlib.util.spec_from_file_location("finrlx_research_env", RESEARCH / "env.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["finrlx_research_env"] = module
    spec.loader.exec_module(module)
    return module


def _rows(n: int, ret: float = 0.01) -> list[dict]:
    return [{"engine_score": 0.2, "realized_return": ret} for _ in range(n)]


def test_the_runner_imports_a_class_that_exists():
    """Guards the exact defect: a name the runner imports must be defined."""
    source = (RESEARCH / "ensemble_runner.py").read_text(encoding="utf-8")
    env_source = (RESEARCH / "env.py").read_text(encoding="utf-8")
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("from env import"):
            imported = stripped.removeprefix("from env import").split("#")[0]
            for name in (n.strip() for n in imported.split(",")):
                assert f"class {name}" in env_source, (
                    f"ensemble_runner imports `{name}` from env.py, which does "
                    "not define it — the producer cannot start"
                )


@needs_gym
def test_episode_returns_exists_and_reports_realised_returns():
    env = _load_env_module().OfflinePortfolioEnv(_rows(30, ret=0.01))
    env.reset()
    done = False
    while not done:
        _, _, done, _, _ = env.step(1)  # baseline exposure 0.8
    series = env.episode_returns()
    assert series, "episode_returns must not be empty after a full episode"
    # return x exposure, not the raw return and not the shaped reward
    assert series[0] == pytest.approx(0.01 * 0.8)


@needs_gym
def test_episode_returns_is_reset_between_episodes():
    env = _load_env_module().OfflinePortfolioEnv(_rows(30))
    env.reset()
    for _ in range(5):
        env.step(1)
    first = len(env.episode_returns())
    env.reset()
    assert env.episode_returns() == [], "a new episode must start with no returns"
    assert first > 0


@needs_gym
def test_synthetic_fallback_is_flagged_so_it_can_be_rejected():
    """A short window pads from a random generator; that must be visible.

    Without the flag, an agent scored on invented rows would enter the
    tournament as if it had learned something from the market.
    """
    mod = _load_env_module()
    short = mod.OfflinePortfolioEnv(_rows(3))  # _max_steps floors at 20
    short.reset()
    done = False
    while not done:
        _, _, done, _, _ = short.step(1)
    assert short.used_synthetic() is True
    assert short.get_metrics()["used_synthetic"] is True


@needs_gym
def test_the_observation_does_not_leak_the_forward_return():
    """No look-ahead: the reward's own return must not appear in the obs.

    The first artifact scored PPO/A2C at Sharpe 4+, because the observation
    carried row[idx].realized_return — the exact forward return step() rewards
    on. The agent saw its answer. The obs at decision time may only contain
    information known BEFORE that return is realised.
    """
    mod = _load_env_module()
    # Rows where the forward return is large and perfectly predictable IF you
    # can see it, but uninformative from the past alone.
    rows = [{"engine_score": 0.0, "realized_return": (0.5 if i % 2 else -0.5),
             "date": f"d{i}", "price": 100.0} for i in range(30)]
    env = mod.OfflinePortfolioEnv(rows)
    obs, _ = env.reset()
    # The initial observation is at idx 0: its lagged return must be 0 (no prior
    # step), NOT row[0].realized_return (+0.5).
    assert abs(float(obs[1])) < 1e-6, "obs leaked the current forward return"

    obs, _, _, _, _ = env.step(1)
    # After one step, idx=1: the lagged return is row[0]'s (+0.5 -> clipped),
    # i.e. the return realised INTO this state, never row[1]'s future return.
    prior = rows[0]["realized_return"]
    import numpy as np
    assert float(obs[1]) == np.clip(prior * 10, -1, 1)


@needs_gym
def test_a_fully_real_episode_is_not_flagged_synthetic():
    mod = _load_env_module()
    env = mod.OfflinePortfolioEnv(_rows(40))
    env.reset()
    done = False
    while not done:
        _, _, done, _, _ = env.step(1)
    assert env.used_synthetic() is False
