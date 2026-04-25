"""RL Gym-like adapter.

Phase 7B.1: lightweight internal adapter with reset/step/observe interface.
Wraps RLEnvironmentService. No external Gym dependency.

Offline/shadow only — does not influence live pipeline.
"""
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.rl_environment import RLEnvironmentService


class RLAdapter:
    """Internal Gym-like adapter for offline RL simulation.

    Usage:
        adapter = RLAdapter(db)
        obs = await adapter.reset(start_date=..., end_date=...)
        while not adapter.done:
            action = agent(obs, adapter.constraints)
            obs, reward, done, info = await adapter.step(action)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._env_svc = RLEnvironmentService(db)
        self._dates: list[date] = []
        self._step_idx: int = 0
        self._universe_id: str | None = None
        self._portfolio_value: float = 100.0
        self._current_weights: dict[str, float] = {}
        self._peak: float = 100.0
        self._state: dict | None = None
        self.done: bool = True
        self.constraints: dict = {}

    async def reset(
        self,
        environment_key: str = "quantpipeline_offline_v1",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        """Reset environment and return initial observation."""
        canonical, _ = self._env_svc.resolve_key(environment_key)
        env_def = await self._env_svc.get_environment_definition(canonical)
        if not env_def:
            await self._env_svc.ensure_default_rl_environment()
            env_def = await self._env_svc.get_environment_definition(canonical)

        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=60)

        self._universe_id = env_def.universe_id if env_def else None
        self.constraints = await self._env_svc._get_policy_constraints()
        self._portfolio_value = 100.0
        self._current_weights = {}
        self._peak = 100.0
        self._step_idx = 0

        # Generate weekly dates
        self._dates = []
        d = start_date
        while d <= end_date:
            if d.weekday() < 5:
                self._dates.append(d)
            d += timedelta(days=7)
            while d.weekday() >= 5:
                d += timedelta(days=1)

        self.done = len(self._dates) < 2
        if self.done:
            self._state = {"assets": [], "tickers": [], "policy_constraints": self.constraints}
            return self._state

        self._state = await self._env_svc.build_state(self._dates[0], self._universe_id)
        return self._state

    async def step(self, action: dict) -> tuple[dict, float, bool, dict]:
        """Execute action, advance to next state. Returns (obs, reward, done, info)."""
        if self.done or self._state is None:
            return self._state or {}, 0.0, True, {"error": "Episode already done"}

        violations = self._env_svc.validate_action(action, self._state)
        new_weights = action.get("target_weights", {})

        # Compute turnover
        turnover = sum(
            abs(new_weights.get(t, 0) - self._current_weights.get(t, 0))
            for t in set(list(new_weights.keys()) + list(self._current_weights.keys()))
        )

        self._current_weights = new_weights
        self._step_idx += 1

        # Advance to next date
        if self._step_idx >= len(self._dates):
            self.done = True
            reward = self._env_svc.compute_reward(
                self._state, action, self._state,
                self._portfolio_value, self._portfolio_value, turnover, violations,
            )
            return self._state, reward, True, {"violations": violations, "turnover": turnover}

        next_state = await self._env_svc.build_state(self._dates[self._step_idx], self._universe_id)

        # Compute portfolio return
        prev_val = self._portfolio_value
        period_return = 0.0
        for a in next_state["assets"]:
            w = self._current_weights.get(a["ticker"], 0)
            prev_price = next(
                (pa["price"] for pa in self._state["assets"] if pa["ticker"] == a["ticker"]),
                None,
            )
            if prev_price and a["price"] and prev_price > 0:
                period_return += w * ((a["price"] - prev_price) / prev_price)
        self._portfolio_value *= (1 + period_return)

        if self._portfolio_value > self._peak:
            self._peak = self._portfolio_value

        reward = self._env_svc.compute_reward(
            self._state, action, next_state,
            prev_val, self._portfolio_value, turnover, violations,
        )

        self._state = next_state
        self.done = self._step_idx >= len(self._dates) - 1

        info = {
            "violations": violations,
            "turnover": round(turnover, 4),
            "portfolio_value": round(self._portfolio_value, 2),
            "step_index": self._step_idx,
        }

        return next_state, reward, self.done, info

    def get_observation(self) -> dict | None:
        return self._state

    @staticmethod
    def get_action_space() -> dict:
        return {
            "fields": ["target_weights", "cash_weight", "action_type"],
            "action_types": ["rebalance", "no_op"],
            "constraints": ["weights_sum_le_1", "no_negative_weights", "position_cap", "cash_floor", "universe_only"],
        }

    @staticmethod
    def get_observation_schema() -> dict:
        return {
            "fields": ["assets", "tickers", "policy_constraints", "as_of_date", "universe_id"],
            "asset_fields": ["asset_id", "ticker", "price", "engine_score"],
        }

    @staticmethod
    def get_reward_schema() -> dict:
        return {
            "formula": "portfolio_return - drawdown_penalty - turnover_penalty - violation_penalty",
            "drawdown_penalty_factor": 2.0,
            "turnover_penalty_factor": 0.001,
            "violation_penalty": 0.05,
        }

    @staticmethod
    def get_adapter_info() -> dict:
        return {
            "adapter_type": "internal_gym_like",
            "supports_reset_step": True,
            "supports_dataset_export": True,
            "supports_policy_evaluation": True,
            "offline_only": True,
            "is_shadow_only": True,
            "live_pipeline_influence": False,
            "no_broker_execution": True,
        }
