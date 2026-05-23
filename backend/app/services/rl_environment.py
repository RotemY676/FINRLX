"""RL environment service.

Phase 7A: offline-only RL environment foundation.
Builds state from market_bars/features/signals/universe/policy.
Validates actions against policy constraints.
Computes reward from portfolio returns with penalties.
Runs offline simulations with baseline/random agents.

Does NOT train RL models or influence live pipeline.
"""
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import gen_uuid
from app.models.ingestion import MarketBar
from app.models.policy import PolicyRule
from app.models.reference import Asset, Universe, UniverseMembership
from app.models.rl import RLEnvironmentDefinition, RLEnvironmentRun, RLEpisode, RLStep
from app.models.signal import SignalOutput, SignalRun
from app.services.rl_agents import AGENTS

DEFAULT_STATE_SCHEMA = {
    "fields": ["asset_returns", "feature_values", "engine_scores", "portfolio_weights",
               "cash_weight", "policy_constraints", "universe_tickers", "data_freshness"],
}
DEFAULT_ACTION_SCHEMA = {
    "fields": ["target_weights", "cash_weight", "action_type"],
    "action_types": ["rebalance", "no_op"],
    "constraints": ["weights_sum_le_1", "no_negative_weights", "position_cap", "cash_floor", "universe_only"],
}
DEFAULT_REWARD_SCHEMA = {
    "formula": "portfolio_return - drawdown_penalty - turnover_penalty - violation_penalty",
    "drawdown_penalty_factor": 2.0,
    "turnover_penalty_factor": 0.001,
    "violation_penalty": 0.05,
}
DEFAULT_CONSTRAINT_SCHEMA = {
    "sources": ["policy_rules"],
    "keys": ["position_cap_max", "cash_floor", "max_invested", "ml_shadow_only"],
}

DEFAULT_ENVIRONMENT_KEY = "quantpipeline_offline_v1"
ENVIRONMENT_ALIASES = {"default": DEFAULT_ENVIRONMENT_KEY}

DEFAULT_ENVIRONMENTS = [
    {
        "key": "quantpipeline_offline_v1",
        "name": "QuantPipeline Offline Environment v1",
        "description": "Offline RL environment using market_bars, features, engine signals, "
                       "and policy constraints. Walk-forward simulation with daily steps. "
                       "Shadow-only — does not influence live pipeline.",
        "state_schema": DEFAULT_STATE_SCHEMA,
        "action_schema": DEFAULT_ACTION_SCHEMA,
        "reward_schema": DEFAULT_REWARD_SCHEMA,
        "constraint_schema": DEFAULT_CONSTRAINT_SCHEMA,
        "status": "active",
        "is_shadow_only": True,
    },
]


class RLEnvironmentService:

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Setup ────────────────────────────────────────────────────────

    async def ensure_default_rl_environment(self) -> int:
        inserted = 0
        # Phase 20.1 — deterministic + active-only default-universe pick.
        uni = (await self.db.execute(
            select(Universe.id)
            .where(Universe.is_active.is_(True))
            .order_by(Universe.created_at.asc())
            .limit(1)
        )).scalar()
        for defn in DEFAULT_ENVIRONMENTS:
            existing = (await self.db.execute(
                select(RLEnvironmentDefinition.id).where(RLEnvironmentDefinition.key == defn["key"])
            )).scalar()
            if not existing:
                self.db.add(RLEnvironmentDefinition(id=gen_uuid(), universe_id=uni, **defn))
                inserted += 1
        if inserted:
            await self.db.commit()
        return inserted

    def resolve_key(self, key: str) -> tuple[str, str | None]:
        """Resolve an environment key, handling aliases like 'default'.

        Returns (canonical_key, warning_or_none).
        """
        canonical = ENVIRONMENT_ALIASES.get(key)
        if canonical:
            return canonical, f"Environment alias '{key}' resolved to '{canonical}'."
        return key, None

    async def get_environment_definitions(self) -> list[RLEnvironmentDefinition]:
        return list((await self.db.execute(
            select(RLEnvironmentDefinition).order_by(RLEnvironmentDefinition.key)
        )).scalars().all())

    async def get_environment_definition(self, key: str) -> RLEnvironmentDefinition | None:
        canonical, _ = self.resolve_key(key)
        return (await self.db.execute(
            select(RLEnvironmentDefinition).where(RLEnvironmentDefinition.key == canonical)
        )).scalar_one_or_none()

    # ── State ────────────────────────────────────────────────────────

    async def _get_policy_constraints(self) -> dict:
        rules = (await self.db.execute(
            select(PolicyRule).where(PolicyRule.is_active == True)  # noqa: E712
        )).scalars().all()
        constraints = {}
        for r in rules:
            if r.threshold_value is not None:
                constraints[r.key] = r.threshold_value
        return constraints

    async def build_state(self, as_of_date: date, universe_id: str | None = None) -> dict:
        """Build environment state for a given date."""
        if not universe_id:
            # Phase 20.1 — deterministic + active-only default-universe pick.
            universe_id = (await self.db.execute(
                select(Universe.id)
                .where(Universe.is_active.is_(True))
                .order_by(Universe.created_at.asc())
                .limit(1)
            )).scalar()

        # Universe assets
        members = (await self.db.execute(
            select(Asset.id, Asset.ticker)
            .join(UniverseMembership, UniverseMembership.asset_id == Asset.id)
            .where(UniverseMembership.universe_id == universe_id)
            .where(UniverseMembership.removed_at.is_(None))
        )).all() if universe_id else []

        assets = []
        for m in members:
            # Price
            price = (await self.db.execute(
                select(MarketBar.close)
                .where(MarketBar.asset_id == m.id)
                .where(MarketBar.bar_date <= as_of_date)
                .order_by(MarketBar.bar_date.desc()).limit(1)
            )).scalar()

            # Latest engine score (deterministic only)
            from app.models.engine import EngineDefinition
            det_keys = (await self.db.execute(
                select(EngineDefinition.key)
                .where(EngineDefinition.is_active == True)  # noqa: E712
                .where(EngineDefinition.category != "ml")
            )).scalars().all()
            avg_score = 0.0
            score_count = 0
            for ek in det_keys:
                run = (await self.db.execute(
                    select(SignalRun.id).where(SignalRun.engine_name == ek)
                    .where(SignalRun.status == "completed")
                    .order_by(SignalRun.run_completed_at.desc()).limit(1)
                )).scalar()
                if run:
                    out = (await self.db.execute(
                        select(SignalOutput.score)
                        .where(SignalOutput.signal_run_id == run)
                        .where(SignalOutput.asset_id == m.id)
                    )).scalar()
                    if out is not None:
                        avg_score += out
                        score_count += 1
            if score_count > 0:
                avg_score /= score_count

            assets.append({
                "asset_id": m.id,
                "ticker": m.ticker,
                "price": price,
                "engine_score": round(avg_score, 4),
            })

        constraints = await self._get_policy_constraints()

        return {
            "as_of_date": as_of_date.isoformat(),
            "universe_id": universe_id,
            "assets": assets,
            "tickers": [a["ticker"] for a in assets],
            "policy_constraints": constraints,
        }

    # ── Action validation ────────────────────────────────────────────

    def validate_action(self, action: dict, state: dict) -> list[str]:
        """Validate an action against policy constraints. Returns list of violations."""
        violations = []
        weights = action.get("target_weights", {})
        cash = action.get("cash_weight", 0)
        constraints = state.get("policy_constraints", {})
        tickers = set(state.get("tickers", []))

        position_cap = constraints.get("position_cap_max", 0.15)
        cash_floor = constraints.get("cash_floor", 0.05)
        max_invested = constraints.get("max_invested", 0.95)

        total = sum(weights.values())
        if total + cash > 1.005:
            violations.append(f"Total allocation {total + cash:.4f} > 1.0")
        for ticker, w in weights.items():
            if w < 0:
                violations.append(f"{ticker}: negative weight {w}")
            if w > position_cap:
                violations.append(f"{ticker}: weight {w:.4f} > position_cap {position_cap}")
            if ticker not in tickers:
                violations.append(f"{ticker}: not in universe")
        if cash < cash_floor:
            violations.append(f"Cash {cash:.4f} < cash_floor {cash_floor}")
        if total > max_invested:
            violations.append(f"Total invested {total:.4f} > max_invested {max_invested}")

        return violations

    # ── Reward ───────────────────────────────────────────────────────

    def compute_reward(self, prev_state: dict, action: dict, next_state: dict,
                       prev_value: float, new_value: float, turnover: float,
                       violations: list[str]) -> float:
        """Compute step reward.

        reward = portfolio_return - drawdown_penalty - turnover_penalty - violation_penalty
        """
        portfolio_return = (new_value - prev_value) / prev_value if prev_value > 0 else 0

        # Drawdown penalty (simplified: penalize negative returns more)
        drawdown_penalty = abs(min(portfolio_return, 0)) * 2.0

        # Turnover penalty
        turnover_penalty = turnover * 0.001

        # Violation penalty
        violation_penalty = len(violations) * 0.05

        return round(portfolio_return - drawdown_penalty - turnover_penalty - violation_penalty, 6)

    # ── Offline simulation ───────────────────────────────────────────

    async def run_offline_simulation(
        self,
        environment_key: str = "quantpipeline_offline_v1",
        start_date: date | None = None,
        end_date: date | None = None,
        agent_type: str = "heuristic_baseline",
    ) -> RLEnvironmentRun:
        """Run an offline simulation episode."""
        now = datetime.now(UTC)
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=60)

        canonical_key, alias_warning = self.resolve_key(environment_key)
        env_def = await self.get_environment_definition(canonical_key)
        if not env_def:
            await self.ensure_default_rl_environment()
            env_def = await self.get_environment_definition(canonical_key)
        environment_key = canonical_key  # persist canonical, not alias

        agent_fn = AGENTS.get(agent_type)
        if not agent_fn:
            agent_fn = AGENTS["heuristic_baseline"]
            agent_type = "heuristic_baseline"

        universe_id = env_def.universe_id if env_def else None
        constraints = await self._get_policy_constraints()
        policy_snapshot = constraints.copy()

        # Create run
        run = RLEnvironmentRun(
            id=gen_uuid(), environment_key=environment_key,
            run_type="simulate", agent_type=agent_type, status="running",
            start_date=start_date, end_date=end_date,
            universe_id=universe_id, policy_snapshot=policy_snapshot,
        )
        self.db.add(run)

        # Generate weekly step dates
        dates = []
        d = start_date
        while d <= end_date:
            if d.weekday() < 5:
                dates.append(d)
            d += timedelta(days=7)
            while d.weekday() >= 5:
                d += timedelta(days=1)

        if len(dates) < 2:
            run.status = "failed"
            run.warnings = ["Insufficient date range"]
            run.completed_at = now
            await self.db.commit()
            return run

        # Episode
        episode = RLEpisode(
            id=gen_uuid(), environment_run_id=run.id, episode_index=0,
            start_date=start_date, end_date=end_date,
            initial_value=100.0, status="running",
        )
        self.db.add(episode)

        portfolio_value = 100.0
        current_weights: dict[str, float] = {}
        peak = 100.0
        max_drawdown = 0.0
        total_reward = 0.0
        total_turnover = 0.0
        warnings: list[str] = []
        if alias_warning:
            warnings.append(alias_warning)
        steps_created = 0

        for i, step_date in enumerate(dates):
            state = await self.build_state(step_date, universe_id)

            # Compute portfolio value from previous weights
            if i > 0 and current_weights:
                new_val = 0.0
                for a in state["assets"]:
                    w = current_weights.get(a["ticker"], 0)
                    if a["price"] and a["price"] > 0:
                        new_val += w * portfolio_value
                    else:
                        new_val += w * portfolio_value
                # Approximate: use price ratios
                prev_state = await self.build_state(dates[i - 1], universe_id)
                period_return = 0.0
                for a in state["assets"]:
                    w = current_weights.get(a["ticker"], 0)
                    prev_price = next((pa["price"] for pa in prev_state["assets"] if pa["ticker"] == a["ticker"]), None)
                    if prev_price and a["price"] and prev_price > 0:
                        period_return += w * ((a["price"] - prev_price) / prev_price)
                portfolio_value *= (1 + period_return)

            if portfolio_value > peak:
                peak = portfolio_value
            dd = (peak - portfolio_value) / peak if peak > 0 else 0
            if dd > max_drawdown:
                max_drawdown = dd

            # Agent action
            action = agent_fn(state, state.get("policy_constraints", {}))
            violations = self.validate_action(action, state)

            # Compute turnover
            new_weights = action.get("target_weights", {})
            turnover = sum(abs(new_weights.get(t, 0) - current_weights.get(t, 0))
                          for t in set(list(new_weights.keys()) + list(current_weights.keys())))
            total_turnover += turnover

            # Reward
            prev_val = portfolio_value
            reward = self.compute_reward(state, action, state, prev_val, portfolio_value, turnover, violations)
            total_reward += reward

            # Store step (compact state — don't store full asset list to save space)
            step = RLStep(
                id=gen_uuid(), episode_id=episode.id, step_index=i,
                as_of_date=step_date,
                state={"tickers": state["tickers"], "asset_count": len(state["assets"])},
                action=action,
                reward=reward,
                portfolio_value=round(portfolio_value, 2),
                cash_weight=action.get("cash_weight", 0),
                exposure=round(sum(new_weights.values()), 4),
                constraint_violations=violations if violations else None,
                metadata_={"agent_type": agent_type, "turnover": round(turnover, 4)},
            )
            self.db.add(step)
            steps_created += 1

            current_weights = new_weights
            if violations:
                for v in violations:
                    if v not in warnings:
                        warnings.append(v)

        total_return = (portfolio_value - 100) / 100

        episode.final_value = round(portfolio_value, 2)
        episode.total_reward = round(total_reward, 4)
        episode.total_return = round(total_return, 4)
        episode.max_drawdown = round(-max_drawdown, 4)
        episode.turnover = round(total_turnover, 4)
        episode.step_count = steps_created
        episode.status = "completed"
        episode.warnings = warnings if warnings else None

        run.status = "completed"
        run.completed_at = datetime.now(UTC)
        run.metrics = {
            "total_return": round(total_return, 4),
            "total_reward": round(total_reward, 4),
            "max_drawdown": round(-max_drawdown, 4),
            "total_turnover": round(total_turnover, 4),
            "step_count": steps_created,
            "agent_type": agent_type,
        }
        run.warnings = warnings if warnings else None

        await self.db.commit()
        return run

    # ── Queries ──────────────────────────────────────────────────────

    async def validate_environment(self, key: str) -> dict:
        canonical_key, alias_warning = self.resolve_key(key)
        env = await self.get_environment_definition(canonical_key)
        if not env:
            return {"valid": False, "environment_key": canonical_key, "errors": ["Environment not found"], "is_shadow_only": True}

        errors = []
        warnings = []
        if alias_warning:
            warnings.append(alias_warning)

        # Check universe exists
        if not env.universe_id:
            errors.append("No universe_id configured")
        else:
            count = (await self.db.execute(
                select(func.count()).select_from(UniverseMembership)
                .where(UniverseMembership.universe_id == env.universe_id)
                .where(UniverseMembership.removed_at.is_(None))
            )).scalar() or 0
            if count == 0:
                errors.append("Universe has no assets")
            elif count < 5:
                warnings.append(f"Universe has only {count} assets")

        # Check market bars exist
        bar_count = (await self.db.execute(select(func.count()).select_from(MarketBar))).scalar() or 0
        if bar_count == 0:
            errors.append("No market bars available")

        return {
            "valid": len(errors) == 0,
            "environment_key": canonical_key,
            "is_shadow_only": env.is_shadow_only if env else True,
            "errors": errors,
            "warnings": warnings,
        }

    async def get_runs(self, limit: int = 20) -> list[RLEnvironmentRun]:
        return list((await self.db.execute(
            select(RLEnvironmentRun).order_by(RLEnvironmentRun.created_at.desc()).limit(limit)
        )).scalars().all())

    async def get_run_detail(self, run_id: str) -> RLEnvironmentRun | None:
        return (await self.db.execute(
            select(RLEnvironmentRun).where(RLEnvironmentRun.id == run_id)
        )).scalar_one_or_none()

    async def get_episodes(self, run_id: str) -> list[RLEpisode]:
        return list((await self.db.execute(
            select(RLEpisode).where(RLEpisode.environment_run_id == run_id)
            .order_by(RLEpisode.episode_index)
        )).scalars().all())

    async def get_steps(self, episode_id: str) -> list[RLStep]:
        return list((await self.db.execute(
            select(RLStep).where(RLStep.episode_id == episode_id)
            .order_by(RLStep.step_index)
        )).scalars().all())

    async def get_status(self) -> dict:
        total_envs = (await self.db.execute(
            select(func.count()).select_from(RLEnvironmentDefinition)
        )).scalar() or 0
        total_runs = (await self.db.execute(
            select(func.count()).select_from(RLEnvironmentRun)
        )).scalar() or 0
        latest = (await self.db.execute(
            select(RLEnvironmentRun).order_by(RLEnvironmentRun.created_at.desc()).limit(1)
        )).scalar_one_or_none()
        return {
            "total_environments": total_envs,
            "total_runs": total_runs,
            "latest_run_id": latest.id if latest else None,
            "latest_run_status": latest.status if latest else None,
            "latest_agent_type": latest.agent_type if latest else None,
            "is_shadow_only": True,
            "live_pipeline_influence": False,
        }
