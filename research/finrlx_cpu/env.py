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
        # Step exactly through the real rows when there are any. The previous
        # `max(len, 20)` floor meant a validation window shorter than 20 states
        # (they are ~18) ran past the real data into the synthetic generator,
        # which the fail-closed guard then rejected — so no real artifact could
        # ever be produced. Only the genuinely-empty case keeps the 20-step
        # demo floor.
        self._max_steps = len(self.dataset) if self.dataset else 20
        self._prev_action = 0
        self._portfolio_value = 1.0
        self._total_reward = 0.0
        self._peak_value = 1.0
        self._max_drawdown = 0.0
        self._turnover_count = 0
        # Per-step portfolio returns for the episode. `ensemble_runner` scores
        # agents on the Sharpe of this series, so it must be the realised
        # return actually achieved (return x exposure), not the raw asset
        # return and not the shaped reward — the turnover penalty is a training
        # signal, not something the portfolio experienced.
        self._episode_returns: list[float] = []
        # True once any step fell back to synthetic rows. An artifact built on
        # a synthetic episode must never be scored as a real result.
        self._used_synthetic = False

    def reset(self, *, seed=None, options=None):
        # Seed the Gymnasium base RNG so the env passes env_checker and SB3's
        # seeding contract; also reseed our own generator for the synthetic
        # fallback path.
        super().reset(seed=seed)
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        self._step_idx = 0
        self._prev_action = 0
        self._portfolio_value = 1.0
        self._total_reward = 0.0
        self._peak_value = 1.0
        self._max_drawdown = 0.0
        self._turnover_count = 0
        self._episode_returns = []
        self._used_synthetic = False
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
        self._episode_returns.append(float(realized_return * exposure))
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
        # After the final step, step_idx == len(dataset); reading a row there
        # would trip the synthetic fallback and falsely flag an otherwise-real
        # episode. The terminal observation is never used for a reward
        # (done=True), so reuse the last real row instead of fabricating one.
        idx = self._step_idx
        if self.dataset:
            idx = min(idx, len(self.dataset) - 1)
        row = self._get_row(idx)

        # NO LOOK-AHEAD. step() rewards on row[idx].realized_return — the
        # FORWARD return from this state. It must never enter the observation,
        # or the agent sees its own answer: the first version did exactly that
        # (Sharpe 4+, a trivial leak, not an edge). The observation at decision
        # time t may contain only information known BEFORE that return is
        # realised:
        #   - engine_score at t: the composite is computed from data up to t.
        #   - the return realised INTO t (the previous row's forward return).
        #   - trailing volatility from prior returns only.
        #   - the previous action.
        engine_score = np.clip(row.get("engine_score", 0.0), -1, 1)

        prev_ret = 0.0
        if self.dataset and idx > 0:
            prev_ret = self.dataset[idx - 1].get("realized_return", 0.0)
        lagged_return = np.clip(prev_ret * 10, -1, 1)

        trailing = [
            self.dataset[j].get("realized_return", 0.0)
            for j in range(max(0, idx - 5), idx)
        ] if self.dataset else []
        vol = float(np.std(trailing)) if len(trailing) >= 2 else 0.0
        volatility = np.clip(vol * 10, 0, 1)

        prev_action_enc = (self._prev_action - 1.0) / 1.0  # maps 0,1,2 -> -1,0,1

        return np.array(
            [engine_score, lagged_return, volatility, prev_action_enc],
            dtype=np.float32,
        )

    def _get_row(self, idx: int) -> dict:
        if self.dataset and 0 <= idx < len(self.dataset):
            return self.dataset[idx]
        # Synthetic fallback. Flagged so any artifact derived from this episode
        # can be rejected upstream rather than scored as a real result.
        self._used_synthetic = True
        return {
            "engine_score": float(self.rng.uniform(-0.3, 0.7)),
            "realized_return": float(self.rng.uniform(-0.03, 0.03)),
        }

    def episode_returns(self) -> list[float]:
        """Per-step realised portfolio returns for the episode just run.

        `ensemble_runner.train_and_score` scores agents on the Sharpe of this
        series. It previously called this method on a class that did not exist
        (`TradingEnv`), so the ensemble producer had never run — see
        `used_synthetic()` for the companion guard.
        """
        return list(self._episode_returns)

    def used_synthetic(self) -> bool:
        """True if any step in this episode came from the synthetic fallback.

        An agent scored on synthetic rows has learned nothing about the market,
        so its Sharpe must never enter the tournament as evidence.
        """
        return self._used_synthetic

    def get_metrics(self) -> dict:
        return {
            "total_reward": round(self._total_reward, 6),
            "final_portfolio_value": round(self._portfolio_value, 6),
            "max_drawdown": round(self._max_drawdown, 6),
            "turnover_count": self._turnover_count,
            "steps": self._step_idx,
            "used_synthetic": self._used_synthetic,
        }
