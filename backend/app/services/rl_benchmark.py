"""RL offline benchmarking and forensic comparison service.

Phase 7C: compares multiple offline/shadow agents on the same dataset/window.
Phase 7G: audit trail, result fingerprint, invariant checks.

Offline/shadow only — does NOT influence live pipeline, publication, or recommendations.
"""
import hashlib
import json
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import gen_uuid
from app.models.ops import AuditEvent
from app.models.rl import (
    RLBenchmarkReport,
    RLEpisode,
    RLPolicySnapshot,
    RLStep,
)
from app.services.rl_agents import AGENTS
from app.services.rl_environment import RLEnvironmentService
from app.services.rl_training import _score_weighted_agent_fn


def _compute_fingerprint(report_data: dict) -> str:
    """Compute deterministic SHA-256 fingerprint from stable benchmark fields."""
    stable = {
        "name": report_data.get("name"),
        "environment_key": report_data.get("environment_key"),
        "start_date": report_data.get("start_date"),
        "end_date": report_data.get("end_date"),
        "requested_agents": report_data.get("requested_agents"),
        "executed_agents": report_data.get("executed_agents"),
        "skipped_agents": report_data.get("skipped_agents"),
        "metrics_by_agent": report_data.get("metrics_by_agent"),
        "reward_breakdown_by_agent": report_data.get("reward_breakdown_by_agent"),
        "safety_flags": report_data.get("safety_flags"),
    }
    serialized = json.dumps(stable, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


def _check_invariants(safety_flags: dict) -> dict:
    """Run lightweight invariant checks on safety flags."""
    checks = {}
    checks["offline_only"] = safety_flags.get("offline_only") is True
    checks["shadow_only"] = safety_flags.get("shadow_only") is True
    checks["no_live_pipeline_influence"] = safety_flags.get("live_pipeline_influence") is False
    checks["no_broker_execution"] = safety_flags.get("no_broker_execution") is True
    checks["no_publication_influence"] = safety_flags.get("no_publication_influence") is True
    checks["no_recommendation_pollution"] = safety_flags.get("no_recommendation_pollution") is True
    checks["all_passed"] = all(checks.values())
    return checks

SAFETY_FLAGS = {
    "offline_only": True,
    "shadow_only": True,
    "live_pipeline_influence": False,
    "no_broker_execution": True,
    "no_publication_influence": True,
    "no_recommendation_pollution": True,
}

DEFAULT_AGENTS_TO_COMPARE = ["heuristic_baseline", "random_valid"]


class RLBenchmarkService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_benchmark(
        self,
        name: str = "Offline Agent Comparison",
        environment_key: str = "quantpipeline_offline_v1",
        start_date: date | None = None,
        end_date: date | None = None,
        agent_keys: list[str] | None = None,
        policy_snapshot_ids: list[str] | None = None,
        ensure_score_weighted_baseline: bool = True,
    ) -> RLBenchmarkReport:
        """Run benchmark comparing multiple agents on the same window."""
        now = datetime.now(UTC)
        env_svc = RLEnvironmentService(self.db)
        canonical_key, _ = env_svc.resolve_key(environment_key)

        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=60)

        env_def = await env_svc.get_environment_definition(canonical_key)
        if not env_def:
            await env_svc.ensure_default_rl_environment()
            env_def = await env_svc.get_environment_definition(canonical_key)
        universe_id = env_def.universe_id if env_def else None

        # Determine agents to compare
        agents_to_run = list(agent_keys or DEFAULT_AGENTS_TO_COMPARE)
        if ensure_score_weighted_baseline and "score_weighted_baseline" not in agents_to_run:
            agents_to_run.append("score_weighted_baseline")

        # Register any policy snapshot agents
        snapshot_agents: dict[str, str] = {}  # temp_key -> snapshot_id
        cleanup_keys: list[str] = []
        if policy_snapshot_ids:
            for sid in policy_snapshot_ids:
                snap = (await self.db.execute(
                    select(RLPolicySnapshot).where(RLPolicySnapshot.id == sid)
                )).scalar_one_or_none()
                if snap and snap.policy_payload and snap.policy_payload.get("weights"):
                    temp_key = f"policy_{sid[:8]}"
                    AGENTS[temp_key] = _score_weighted_agent_fn(snap.policy_payload["weights"])
                    agents_to_run.append(temp_key)
                    snapshot_agents[temp_key] = sid
                    cleanup_keys.append(temp_key)

        report = RLBenchmarkReport(
            id=gen_uuid(), name=name, environment_key=canonical_key,
            universe_id=universe_id, start_date=start_date, end_date=end_date,
            status="running", compared_agents=agents_to_run,
            policy_snapshot_ids=policy_snapshot_ids,
            safety_flags=SAFETY_FLAGS,
            dataset_lineage={"environment_key": canonical_key, "start": start_date.isoformat(), "end": end_date.isoformat()},
        )
        self.db.add(report)

        # Audit: benchmark_run_requested
        self.db.add(AuditEvent(
            id=gen_uuid(), actor="system", action="benchmark_run_requested",
            object_type="rl_benchmark", object_id=report.id,
            details={
                "event_type": "benchmark_run_requested",
                "actor_type": "api", "source": "rl_benchmark",
                "name": name, "environment_key": canonical_key,
                "start_date": start_date.isoformat(), "end_date": end_date.isoformat(),
                "requested_agents": agents_to_run,
                "safety_flags": SAFETY_FLAGS,
            },
            occurred_at=now,
        ))

        metrics_by_agent: dict[str, dict] = {}
        reward_breakdown: dict[str, dict] = {}
        violations_by_agent: dict[str, list] = {}
        sim_run_ids: dict[str, str] = {}
        forensic_rows: list[dict] = []
        forensic_by_agent: dict[str, list[dict]] = {}
        warnings: list[str] = []
        executed_agents: list[str] = []
        skipped_agents: list[dict] = []

        try:
            for agent_key in agents_to_run:
                if agent_key not in AGENTS:
                    skipped_agents.append({"agent_key": agent_key, "reason": f"Agent '{agent_key}' not found"})
                    warnings.append(f"Agent '{agent_key}' not found — skipped")
                    continue

                sim = await env_svc.run_offline_simulation(
                    canonical_key, start_date, end_date, agent_key,
                )
                sim_run_ids[agent_key] = sim.id
                executed_agents.append(agent_key)
                m = sim.metrics or {}

                metrics_by_agent[agent_key] = {
                    "total_return": m.get("total_return"),
                    "total_reward": m.get("total_reward"),
                    "max_drawdown": m.get("max_drawdown"),
                    "total_turnover": m.get("total_turnover"),
                    "step_count": m.get("step_count"),
                    "status": sim.status,
                }

                # Compute reward breakdown from simulation metrics
                tr = m.get("total_return", 0) or 0
                dd = m.get("max_drawdown", 0) or 0
                to = m.get("total_turnover", 0) or 0
                reward_breakdown[agent_key] = {
                    "portfolio_return_component": round(tr, 6),
                    "drawdown_penalty_component": round(abs(min(dd, 0)) * 2.0, 6),
                    "turnover_penalty_component": round(to * 0.001, 6),
                }

                # Collect violations from steps
                episodes = (await self.db.execute(
                    select(RLEpisode).where(RLEpisode.environment_run_id == sim.id)
                )).scalars().all()
                agent_violations: list[str] = []
                agent_forensic: list[dict] = []
                for ep in episodes:
                    steps = (await self.db.execute(
                        select(RLStep).where(RLStep.episode_id == ep.id)
                        .order_by(RLStep.step_index)
                    )).scalars().all()
                    for s in steps:
                        if s.constraint_violations:
                            agent_violations.extend(s.constraint_violations)
                        row = {
                            "step_index": s.step_index,
                            "as_of_date": s.as_of_date.isoformat() if s.as_of_date else None,
                            "agent_key": agent_key,
                            "reward": s.reward,
                            "portfolio_value": s.portfolio_value,
                            "turnover": (s.metadata_ or {}).get("turnover"),
                            "violations": s.constraint_violations,
                            "action_type": (s.action or {}).get("action_type"),
                        }
                        agent_forensic.append(row)
                        if agent_key == agents_to_run[0]:
                            forensic_rows.append(row)
                forensic_by_agent[agent_key] = agent_forensic[:50]  # cap at 50 per agent

                violations_by_agent[agent_key] = agent_violations
                metrics_by_agent[agent_key]["violation_count"] = len(agent_violations)

                if sim.warnings:
                    for w in sim.warnings:
                        if w not in warnings:
                            warnings.append(w)
        finally:
            # Clean up temporary agents
            for k in cleanup_keys:
                AGENTS.pop(k, None)

        is_complete = len(skipped_agents) == 0 and len(executed_agents) == len(agents_to_run)
        report.status = "completed" if is_complete else "partial"
        report.completed_at = datetime.now(UTC)
        report.compared_agents = executed_agents  # only agents that actually ran
        report.metrics_by_agent = metrics_by_agent
        report.reward_breakdown_by_agent = reward_breakdown
        report.violations_by_agent = {k: v[:20] for k, v in violations_by_agent.items()}
        report.simulation_run_ids = sim_run_ids
        report.forensic_summary = forensic_rows[:100]
        report.warnings = warnings if warnings else None
        report.dataset_lineage = {
            "environment_key": canonical_key,
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "requested_agents": agents_to_run,
            "executed_agents": executed_agents,
            "skipped_agents": skipped_agents,
            "is_complete_comparison": is_complete,
            "forensic_summary_by_agent": forensic_by_agent,
        }

        # Compute fingerprint and invariant checks
        fingerprint_data = {
            "name": name, "environment_key": canonical_key,
            "start_date": start_date.isoformat(), "end_date": end_date.isoformat(),
            "requested_agents": agents_to_run, "executed_agents": executed_agents,
            "skipped_agents": skipped_agents,
            "metrics_by_agent": metrics_by_agent,
            "reward_breakdown_by_agent": reward_breakdown,
            "safety_flags": SAFETY_FLAGS,
        }
        result_fingerprint = _compute_fingerprint(fingerprint_data)
        invariant_checks = _check_invariants(SAFETY_FLAGS)

        # Store governance fields in dataset_lineage
        report.dataset_lineage["result_fingerprint"] = result_fingerprint
        report.dataset_lineage["invariant_check_results"] = invariant_checks

        # Audit: benchmark_run_completed / partial / failed
        event_type = f"benchmark_run_{report.status}"
        self.db.add(AuditEvent(
            id=gen_uuid(), actor="system", action=event_type,
            object_type="rl_benchmark", object_id=report.id,
            details={
                "event_type": event_type,
                "actor_type": "api", "source": "rl_benchmark",
                "benchmark_report_id": report.id,
                "status": report.status,
                "is_complete_comparison": is_complete,
                "requested_agents": agents_to_run,
                "executed_agents": executed_agents,
                "skipped_agents": skipped_agents,
                "safety_flags": SAFETY_FLAGS,
                "result_fingerprint": result_fingerprint,
                "invariant_check_results": invariant_checks,
                "warnings": warnings,
            },
            occurred_at=datetime.now(UTC),
        ))

        await self.db.commit()
        return report

    async def compare_policy(
        self,
        policy_snapshot_id: str,
        environment_key: str = "quantpipeline_offline_v1",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> RLBenchmarkReport:
        """Compare a policy snapshot against baseline agents."""
        return await self.run_benchmark(
            name=f"Policy comparison — {policy_snapshot_id[:8]}",
            environment_key=environment_key,
            start_date=start_date, end_date=end_date,
            agent_keys=["heuristic_baseline", "random_valid"],
            policy_snapshot_ids=[policy_snapshot_id],
        )

    async def get_benchmarks(self, limit: int = 20) -> list[RLBenchmarkReport]:
        return list((await self.db.execute(
            select(RLBenchmarkReport).order_by(RLBenchmarkReport.created_at.desc()).limit(limit)
        )).scalars().all())

    async def get_benchmark(self, report_id: str) -> RLBenchmarkReport | None:
        return (await self.db.execute(
            select(RLBenchmarkReport).where(RLBenchmarkReport.id == report_id)
        )).scalar_one_or_none()

    async def get_audit_events(self, limit: int = 20) -> list[AuditEvent]:
        return list((await self.db.execute(
            select(AuditEvent)
            .where(AuditEvent.object_type == "rl_benchmark")
            .order_by(AuditEvent.occurred_at.desc()).limit(limit)
        )).scalars().all())

    async def get_audit_for_report(self, report_id: str) -> list[AuditEvent]:
        return list((await self.db.execute(
            select(AuditEvent)
            .where(AuditEvent.object_type == "rl_benchmark")
            .where(AuditEvent.object_id == report_id)
            .order_by(AuditEvent.occurred_at.desc())
        )).scalars().all())

    async def get_audit_event(self, event_id: str) -> AuditEvent | None:
        return (await self.db.execute(
            select(AuditEvent).where(AuditEvent.id == event_id)
            .where(AuditEvent.object_type == "rl_benchmark")
        )).scalar_one_or_none()

    async def get_ops_summary(self) -> dict:
        total = (await self.db.execute(
            select(func.count()).select_from(RLBenchmarkReport)
        )).scalar() or 0
        latest = (await self.db.execute(
            select(RLBenchmarkReport).order_by(RLBenchmarkReport.created_at.desc()).limit(1)
        )).scalar_one_or_none()
        return {
            "total_benchmarks": total,
            "latest_benchmark_status": latest.status if latest else None,
            "latest_benchmark_agents": len(latest.compared_agents or []) if latest else 0,
        }
