"""Tiny Gymnasium-compatible offline portfolio environment for CPU RL research.

LOCAL RESEARCH ONLY — not used by production.
No broker execution, no live RL, no production influence.
"""

import numpy as np
import gymnasium as gym
from gymnasium import spaces


class OfflinePortfolioEnv(gym.Env):
    """Minimal offline portfolio environment for CPU PPO/A2C research.

    Actions (discrete):
        0 = neutral / cash-like (low exposure)
        1 = baseline exposure (proportional to engine scores)
        2 = risk-reduced exposure (dampened)

    Observation:
        [engine_score, lagged_return, volatility_proxy, previous_action_encoded]

    Reward:
        realized_return * exposure - turnover_penalty
    """

    metadata = {"render_modes": []}

    def __init__(self, dataset: list[dict] | None = None, seed: int = 42):
        super().__init__()
        self.dataset = dataset or []
        self._seed = seed
        self.rng = np.random.default_rng(seed)

        self.observation_space = spaces.Box(
            low=-1.0, high=1.0, shape=(4,), dtype=np.float32,
        )
        self.action_space = spaces.Discrete(3)

        self._step_idx = 0
        self._max_steps = max(len(self.dataset), 20)
        self._prev_action = 0
        self._portfolio_value = 1.0
        self._total_reward = 0.0
        self._peak_value = 1.0
        self._max_drawdown = 0.0
        self._turnover_count = 0

    def reset(self, *, seed=None, options=None):
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        self._step_idx = 0
        self._prev_action = 0
        self._portfolio_value = 1.0
        self._total_reward = 0.0
        self._peak_value = 1.0
        self._max_drawdown = 0.0
        self._turnover_count = 0
        return self._get_obs(), {}

    def step(self, action: int):
        row = self._get_row(self._step_idx)

        engine_score = row.get("engine_score", 0.0)
        realized_return = row.get("realized_return", 0.0)

        # Exposure based on action
        if action == 0:
            exposure = 0.1  # mostly cash
        elif action == 1:
            exposure = 0.8  # baseline
        else:
            exposure = 0.4  # risk-reduced

        # Turnover penalty
        turnover_penalty = 0.001 if action != self._prev_action else 0.0
        if action != self._prev_action:
            self._turnover_count += 1

        # Reward
        reward = float(realized_return * exposure - turnover_penalty)
        self._total_reward += reward

        # Portfolio tracking
        self._portfolio_value *= (1.0 + realized_return * exposure)
        self._peak_value = max(self._peak_value, self._portfolio_value)
        dd = (self._peak_value - self._portfolio_value) / self._peak_value if self._peak_value > 0 else 0.0
        self._max_drawdown = max(self._max_drawdown, dd)

        self._prev_action = action
        self._step_idx += 1
        done = self._step_idx >= self._max_steps

        return self._get_obs(), reward, done, False, {
            "portfolio_value": self._portfolio_value,
            "max_drawdown": self._max_drawdown,
        }

    def _get_obs(self) -> np.ndarray:
        row = self._get_row(self._step_idx)
        engine_score = np.clip(row.get("engine_score", 0.0), -1, 1)
        lagged_return = np.clip(row.get("realized_return", 0.0) * 10, -1, 1)
        volatility = np.clip(abs(row.get("realized_return", 0.0)) * 5, 0, 1)
        prev_action_enc = (self._prev_action - 1.0) / 1.0  # maps 0,1,2 -> -1,0,1

        return np.array(
            [engine_score, lagged_return, volatility, prev_action_enc],
            dtype=np.float32,
        )

    def _get_row(self, idx: int) -> dict:
        if self.dataset and 0 <= idx < len(self.dataset):
            return self.dataset[idx]
        # Synthetic fallback
        return {
            "engine_score": float(self.rng.uniform(-0.3, 0.7)),
            "realized_return": float(self.rng.uniform(-0.03, 0.03)),
        }

    def get_metrics(self) -> dict:
        return {
            "total_reward": round(self._total_reward, 6),
            "final_portfolio_value": round(self._portfolio_value, 6),
            "max_drawdown": round(self._max_drawdown, 6),
            "turnover_count": self._turnover_count,
            "steps": self._step_idx,
        }
