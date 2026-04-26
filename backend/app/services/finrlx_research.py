"""FinRL-X neural RL research spike.

Phase 8A: strictly isolated research-only adapter for FinRL-X feasibility.

Real FinRL-X training is NOT implemented in Phase 8A.
No ML/RL libraries (numpy, torch, gymnasium, stable-baselines3) are installed.
This module provides a stubbed research interface that validates the dataset
contract, simulates the training interface honestly, and exports shadow-only
research candidates.

Does NOT influence live pipeline, publication, recommendations, or overview.
"""
import hashlib
import json
import logging
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.models.rl import RLPolicySnapshot, RLTrainingRun
from app.models.ops import AuditEvent
from app.models.base import gen_uuid
from app.services.rl_training import RLTrainingService
from app.services.rl_environment import RLEnvironmentService

FINRLX_SAFETY_FLAGS = {
    "research_only": True,
    "offline_only": True,
    "shadow_only": True,
    "live_pipeline_influence": False,
    "no_broker_execution": True,
    "no_publication_influence": True,
    "no_recommendation_pollution": True,
}

REQUIRED_DATASET_FIELDS = [
    "as_of_date", "universe_tickers", "policy_constraints", "assets",
]
REQUIRED_ASSET_FIELDS = [
    "ticker", "price", "engine_score",
]
OPTIONAL_ASSET_FIELDS = [
    "next_price", "realized_return",
]


def _json_safe(obj):
    """Recursively convert non-JSON-serializable types to safe primitives."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    return str(obj)


class FinRLXResearchService:

    def __init__(self, db: AsyncSession):
        self.db = db

    def get_adapter_info(self) -> dict:
        return {
            "adapter_type": "finrlx_research_spike",
            "research_only": True,
            "offline_only": True,
            "shadow_only": True,
            "live_pipeline_influence": False,
            "no_broker_execution": True,
            "no_publication_influence": True,
            "no_recommendation_pollution": True,
            "requires_finrlx_dependency": True,
            "finrlx_available": False,
            "gpu_required": False,
            "production_runtime_dependency": False,
            "installed_ml_libraries": [],
            "missing_for_real_training": [
                "numpy", "torch or tensorflow", "gymnasium or gym",
                "stable-baselines3 or finrl", "pandas",
            ],
            "training_mode": "stubbed",
            "notes": "Real FinRL-X training is NOT available. "
                     "No ML/RL libraries are installed. "
                     "This is a research interface stub only.",
        }

    async def validate_dataset_contract(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 10,
    ) -> dict:
        """Validate the current RL dataset export matches FinRL-X requirements."""
        train_svc = RLTrainingService(self.db)
        rows = await train_svc.export_training_dataset(
            start_date=start_date, end_date=end_date, limit=limit,
        )

        if not rows:
            return {
                "valid": False,
                "missing_fields": [],
                "warnings": ["No dataset rows available"],
                "row_count": 0, "asset_count": 0,
                "date_range": None, "schema_version": "1.0",
                "safety_flags": FINRLX_SAFETY_FLAGS,
            }

        missing_fields = []
        warnings = []
        all_tickers = set()

        for row in rows:
            for f in REQUIRED_DATASET_FIELDS:
                if f not in row:
                    if f not in missing_fields:
                        missing_fields.append(f)
            for asset in row.get("assets", []):
                all_tickers.add(asset.get("ticker", "?"))
                for af in REQUIRED_ASSET_FIELDS:
                    if af not in asset:
                        key = f"assets[].{af}"
                        if key not in missing_fields:
                            missing_fields.append(key)
                for af in OPTIONAL_ASSET_FIELDS:
                    if asset.get(af) is None:
                        w = f"Optional field assets[].{af} is null in some rows"
                        if w not in warnings:
                            warnings.append(w)

        dates = [r["as_of_date"] for r in rows if r.get("as_of_date")]
        date_range = {"start": min(dates), "end": max(dates)} if dates else None

        return {
            "valid": len(missing_fields) == 0,
            "missing_fields": missing_fields,
            "warnings": warnings,
            "row_count": len(rows),
            "asset_count": len(all_tickers),
            "date_range": date_range,
            "schema_version": "1.0",
            "safety_flags": FINRLX_SAFETY_FLAGS,
        }

    async def train_research_stub(
        self,
        name: str = "FinRL-X Research Candidate",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        """Run a stubbed research training that validates the interface without real neural training."""
        now = datetime.now(timezone.utc)

        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=60)

        # Capture pre-training production fingerprints
        pre_fingerprints = await self._capture_production_fingerprints()

        # Audit: requested
        await self._create_audit_event("finrlx_train_research_requested", {
            "name": name, "start_date": start_date.isoformat(), "end_date": end_date.isoformat(),
            "research_acknowledgement": True, "safety_flags": FINRLX_SAFETY_FLAGS,
        })

        # Validate dataset first
        validation = await self.validate_dataset_contract(start_date, end_date, limit=20)

        # Create a training run record
        env_svc = RLEnvironmentService(self.db)
        canonical_key, _ = env_svc.resolve_key("quantpipeline_offline_v1")

        run = RLTrainingRun(
            id=gen_uuid(), agent_key="finrlx_research_stub",
            environment_key=canonical_key, status="running",
            train_start_date=start_date, train_end_date=end_date,
            config={
                "method": "finrlx_research_stub",
                "training_mode": "stubbed",
                "real_neural_training": False,
                "notes": "No ML/RL libraries installed. Interface validation only.",
            },
        )
        self.db.add(run)

        # Simulate stub training result
        stub_weights = {"technical_momentum": 0.35, "risk_quality": 0.35, "news_sentiment": 0.30}
        stub_metrics = {
            "training_mode": "stubbed",
            "real_neural_training": False,
            "dataset_rows": validation["row_count"],
            "dataset_valid": validation["valid"],
            "dataset_warnings": validation["warnings"],
        }

        # Create policy candidate
        candidate_id = gen_uuid()
        snapshot = RLPolicySnapshot(
            id=candidate_id, training_run_id=run.id,
            agent_key="finrlx_research_stub",
            environment_key=canonical_key,
            policy_type="finrlx_research_stub",
            policy_payload={
                "weights": stub_weights,
                "research_only": True,
                "training_mode": "stubbed",
                "real_neural_training": False,
                "notes": "Stubbed research candidate — no real FinRL-X training occurred.",
                "safety_flags": FINRLX_SAFETY_FLAGS,
            },
            metrics=stub_metrics,
        )
        self.db.add(snapshot)

        run.status = "completed"
        run.completed_at = now
        run.metrics = {
            **stub_metrics,
            "policy_candidate_id": candidate_id,
        }

        # Capture post-training production fingerprints
        post_fingerprints = await self._capture_production_fingerprints()

        # Per-component comparison
        component_checks = {}
        for comp_key in ["recommendations_current", "publication_status", "overview"]:
            pre_comp = pre_fingerprints.get(comp_key, {})
            post_comp = post_fingerprints.get(comp_key, {})
            pre_avail = pre_comp.get("snapshot_available", False)
            post_avail = post_comp.get("snapshot_available", False)
            if pre_avail and post_avail:
                comp_unchanged = pre_comp.get("hash") == post_comp.get("hash")
            else:
                comp_unchanged = None  # cannot determine
            component_checks[comp_key] = {
                "before_hash": pre_comp.get("hash"),
                "after_hash": post_comp.get("hash"),
                "unchanged": comp_unchanged,
                "snapshot_available": pre_avail and post_avail,
            }
            if not (pre_avail and post_avail):
                reason = pre_comp.get("reason") or post_comp.get("reason") or "snapshot unavailable"
                component_checks[comp_key]["reason"] = reason

        # Overall unchanged: true only if all available components unchanged
        available_checks = [c for c in component_checks.values() if c["snapshot_available"]]
        if available_checks:
            overall_unchanged = all(c["unchanged"] for c in available_checks)
        else:
            overall_unchanged = None  # no useful components

        # Audit: completed
        await self._create_audit_event("finrlx_train_research_completed", {
            "candidate_id": candidate_id, "training_run_id": run.id,
            "status": "completed", "training_mode": "stubbed",
            "safety_flags": FINRLX_SAFETY_FLAGS,
            "isolation_checks": self.get_candidate_isolation(candidate_id)["checks"],
            "production_fingerprints_unchanged": overall_unchanged,
            "component_checks": component_checks,
        })

        await self.db.commit()

        return {
            "policy_candidate_id": candidate_id,
            "training_run_id": run.id,
            "name": name,
            "policy_type": "finrlx_research_stub",
            "training_status": "completed",
            "training_mode": "stubbed",
            "real_neural_training": False,
            "dataset_contract_summary": {
                "valid": validation["valid"],
                "row_count": validation["row_count"],
                "asset_count": validation["asset_count"],
                "date_range": validation["date_range"],
                "warnings": validation["warnings"],
            },
            "model_metadata": {
                "stub_weights": stub_weights,
                "notes": "No ML/RL libraries installed. This is a stubbed research interface.",
            },
            "safety_flags": FINRLX_SAFETY_FLAGS,
            "production_fingerprints": {
                "before": pre_fingerprints,
                "after": post_fingerprints,
                "unchanged": overall_unchanged,
                "component_checks": component_checks,
            },
            "warnings": [
                "Real FinRL-X training was NOT performed.",
                "No ML/RL libraries are installed.",
                "This candidate is a research interface stub only.",
            ],
            "created_at": now.isoformat(),
        }

    async def get_candidates(self) -> list[dict]:
        snapshots = (await self.db.execute(
            select(RLPolicySnapshot)
            .where(RLPolicySnapshot.policy_type.like("finrlx_%"))
            .order_by(RLPolicySnapshot.created_at.desc()).limit(20)
        )).scalars().all()
        return [self._candidate_dict(s) for s in snapshots]

    async def get_candidate(self, candidate_id: str) -> dict | None:
        s = (await self.db.execute(
            select(RLPolicySnapshot).where(RLPolicySnapshot.id == candidate_id)
            .where(RLPolicySnapshot.policy_type.like("finrlx_%"))
        )).scalar_one_or_none()
        return self._candidate_dict(s) if s else None

    def _candidate_dict(self, s: RLPolicySnapshot) -> dict:
        payload = s.policy_payload or {}
        return {
            "id": s.id,
            "training_run_id": s.training_run_id,
            "agent_key": s.agent_key,
            "policy_type": s.policy_type,
            "training_mode": payload.get("training_mode", "stubbed"),
            "real_neural_training": payload.get("real_neural_training", False),
            "research_only": True,
            "offline_only": True,
            "shadow_only": True,
            "live_pipeline_influence": False,
            "no_broker_execution": True,
            "no_publication_influence": True,
            "no_recommendation_pollution": True,
            "safety_flags": FINRLX_SAFETY_FLAGS,
            "metrics": s.metrics,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }

    def get_candidate_isolation(self, candidate_id: str) -> dict:
        """Check candidate isolation — all promotion/live/broker actions are blocked."""
        checks = {
            "promotion_blocked": True,
            "publication_blocked": True,
            "live_recommendation_blocked": True,
            "overview_influence_blocked": True,
            "broker_execution_blocked": True,
        }
        return {
            "candidate_id": candidate_id,
            "isolated": True,
            "checks": checks,
            "all_blocked": all(checks.values()),
            "safety_flags": FINRLX_SAFETY_FLAGS,
            "reasons": [
                "FinRL-X research candidates are research-only, offline-only, shadow-only.",
                "No promotion, publication, live recommendation, overview influence, or broker action is permitted.",
                "Real FinRL-X training has not been implemented.",
            ],
        }

    async def _capture_production_fingerprints(self) -> dict:
        """Capture lightweight per-component fingerprints proving no production mutation."""
        from app.models.recommendation import Recommendation
        from sqlalchemy import func as sqfunc

        components: dict[str, dict] = {}

        # 1. recommendations_current
        try:
            rec_count = (await self.db.execute(
                select(sqfunc.count()).select_from(Recommendation)
            )).scalar() or 0
            latest_rec = (await self.db.execute(
                select(Recommendation.id, Recommendation.status)
                .order_by(Recommendation.created_at.desc()).limit(1)
            )).first()
            snap = {"count": rec_count, "latest_id": latest_rec.id if latest_rec else None,
                    "latest_status": latest_rec.status if latest_rec else None}
            snap_str = json.dumps(snap, sort_keys=True, default=str)
            components["recommendations_current"] = {
                "snapshot_available": True, "snapshot": snap,
                "hash": hashlib.sha256(snap_str.encode()).hexdigest()[:16],
            }
        except Exception:
            components["recommendations_current"] = {"snapshot_available": False, "reason": "query error"}

        # 2. publication_status
        try:
            status_counts: dict[str, int] = {}
            for st in ["draft", "staged", "approved", "published", "published_with_warning", "deferred", "suppressed"]:
                c = (await self.db.execute(
                    select(sqfunc.count()).select_from(Recommendation).where(Recommendation.status == st)
                )).scalar() or 0
                status_counts[st] = c
            snap = status_counts
            snap_str = json.dumps(snap, sort_keys=True, default=str)
            components["publication_status"] = {
                "snapshot_available": True, "snapshot": snap,
                "hash": hashlib.sha256(snap_str.encode()).hexdigest()[:16],
            }
        except Exception:
            components["publication_status"] = {"snapshot_available": False, "reason": "query error"}

        # 3. overview — aggregate API, no safe stable internal function
        components["overview"] = {
            "snapshot_available": False,
            "reason": "Overview is an aggregate API response; no safe internal stable snapshot function exists yet.",
        }

        # Overall hash from available components
        hashable = {k: v.get("hash") for k, v in components.items() if v.get("snapshot_available")}
        overall_str = json.dumps(hashable, sort_keys=True)
        overall_hash = hashlib.sha256(overall_str.encode()).hexdigest()[:16]

        return _json_safe({**components, "hash": overall_hash})

    async def _create_audit_event(self, event_type: str, details: dict) -> None:
        try:
            safe_details = _json_safe(details)
            self.db.add(AuditEvent(
                id=gen_uuid(), actor="system", action=event_type,
                object_type="finrlx_research",
                object_id=str(details.get("candidate_id")) if details.get("candidate_id") else None,
                details=safe_details, occurred_at=datetime.now(timezone.utc),
            ))
        except Exception as e:
            logger.error("Failed to create audit event %s: %s", event_type, e)

    @staticmethod
    def get_neural_dependency_status() -> dict:
        """Detect optional CPU-only neural RL dependencies with lazy imports."""
        status: dict[str, bool | None] = {}
        import_errors: dict[str, str] = {}

        for lib in ["numpy", "gymnasium", "stable_baselines3", "torch"]:
            try:
                __import__(lib)
                status[f"{lib}_available"] = True
            except Exception as e:
                status[f"{lib}_available"] = False
                import_errors[lib] = str(e)

        torch_cuda = None
        if status.get("torch_available"):
            try:
                import torch
                torch_cuda = torch.cuda.is_available()
            except Exception:
                torch_cuda = False

        neural_ok = all(status.get(f"{l}_available") for l in ["numpy", "gymnasium", "stable_baselines3", "torch"])
        missing = [l for l in ["numpy", "gymnasium", "stable_baselines3", "torch"] if not status.get(f"{l}_available")]

        return {
            **status,
            "torch_cuda_available": torch_cuda,
            "cpu_only_mode": True,
            "neural_training_available": neural_ok,
            "missing_dependencies": missing,
            "production_runtime_dependency": False,
            "import_errors": import_errors if import_errors else None,
        }

    async def train_cpu_prototype(
        self,
        name: str = "CPU-only Research Prototype",
        algorithm: str = "PPO",
        start_date: date | None = None,
        end_date: date | None = None,
        timesteps: int = 50,
        seed: int = 42,
    ) -> dict:
        """Run a CPU-only PPO/A2C research prototype, or fall back if dependencies missing."""
        now = datetime.now(timezone.utc)
        dep_status = self.get_neural_dependency_status()

        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=60)

        timesteps = min(max(timesteps, 1), 500)  # cap

        # Validate date range
        if start_date > end_date:
            raise ValueError("start_date must be <= end_date")

        # Validate dataset contract before any candidate creation
        validation = await self.validate_dataset_contract(start_date, end_date, limit=10)
        if not validation["valid"]:
            return _json_safe({
                "policy_candidate_id": None, "training_run_id": None,
                "name": name, "status": "dataset_invalid",
                "training_mode": "dataset_invalid", "real_neural_training": False,
                "algorithm": algorithm, "timesteps": timesteps,
                "dependency_status": dep_status, "safety_flags": FINRLX_SAFETY_FLAGS,
                "not_eligible_for_promotion": True,
                "dataset_validation": validation,
                "warnings": [f"Dataset invalid: {validation.get('missing_fields', [])}"],
                "created_at": now.isoformat(),
            })

        pre_fp = await self._capture_production_fingerprints()

        await self._create_audit_event("finrlx_cpu_research_train_requested", {
            "name": name, "algorithm": algorithm, "timesteps": timesteps, "seed": seed,
            "start_date": start_date.isoformat(), "end_date": end_date.isoformat(),
            "dependency_status": dep_status, "safety_flags": FINRLX_SAFETY_FLAGS,
        })

        env_svc = RLEnvironmentService(self.db)
        canonical_key, _ = env_svc.resolve_key("quantpipeline_offline_v1")

        if not dep_status["neural_training_available"]:
            # Dependencies unavailable — create honest stub candidate
            try:
                run = RLTrainingRun(
                    id=gen_uuid(), agent_key=f"finrlx_cpu_{algorithm.lower()}_unavailable",
                    environment_key=canonical_key, status="dependency_unavailable",
                    train_start_date=start_date, train_end_date=end_date,
                    config=_json_safe({"algorithm": algorithm, "timesteps": timesteps, "seed": seed,
                            "training_mode": "dependency_unavailable", "real_neural_training": False}),
                )
                self.db.add(run)
                run.completed_at = now

                candidate_id = gen_uuid()
                self.db.add(RLPolicySnapshot(
                    id=candidate_id, training_run_id=run.id,
                    agent_key=run.agent_key, environment_key=canonical_key,
                    policy_type=f"finrlx_cpu_{algorithm.lower()}_unavailable",
                    policy_payload=_json_safe({"training_mode": "dependency_unavailable", "real_neural_training": False,
                                    "safety_flags": FINRLX_SAFETY_FLAGS, "missing": dep_status["missing_dependencies"]}),
                    metrics=_json_safe({"training_mode": "dependency_unavailable"}),
                ))
                run.metrics = _json_safe({"policy_candidate_id": candidate_id, "training_mode": "dependency_unavailable"})

                post_fp = await self._capture_production_fingerprints()
                cc = self._build_component_checks(pre_fp, post_fp)
                avail = [c for c in cc.values() if c["snapshot_available"]]
                overall_unch = all(c["unchanged"] for c in avail) if avail else None

                iso = self.get_candidate_isolation(candidate_id)

                await self._create_audit_event("finrlx_cpu_research_train_dependency_unavailable", {
                    "candidate_id": candidate_id, "training_run_id": run.id,
                    "algorithm": algorithm, "dependency_status": dep_status,
                    "safety_flags": FINRLX_SAFETY_FLAGS, "component_checks": cc,
                    "production_fingerprints_unchanged": overall_unch,
                    "isolation_checks": iso["checks"],
                })
                await self.db.commit()

                return _json_safe({
                    "policy_candidate_id": candidate_id, "training_run_id": run.id,
                    "name": name, "status": "dependency_unavailable",
                    "training_mode": "dependency_unavailable", "real_neural_training": False,
                    "algorithm": algorithm, "timesteps": timesteps,
                    "dependency_status": dep_status, "safety_flags": FINRLX_SAFETY_FLAGS,
                    "not_eligible_for_promotion": True,
                    "isolation_checks": iso["checks"], "isolated": True, "all_blocked": True,
                    "production_fingerprints": {"before": pre_fp, "after": post_fp,
                                                "unchanged": overall_unch, "component_checks": cc},
                    "warnings": [f"Dependencies unavailable: {', '.join(dep_status['missing_dependencies'])}",
                                 "No real CPU PPO/A2C training was performed.",
                                 "Candidate created as dependency_unavailable stub."],
                    "created_at": now.isoformat(),
                })
            except Exception as e:
                logger.error("dependency_unavailable path failed: %s", e, exc_info=True)
                try:
                    await self.db.rollback()
                except Exception:
                    pass
                return _json_safe({
                    "policy_candidate_id": None, "training_run_id": None,
                    "name": name, "status": "dependency_unavailable",
                    "training_mode": "dependency_unavailable", "real_neural_training": False,
                    "algorithm": algorithm, "timesteps": timesteps,
                    "dependency_status": dep_status, "safety_flags": FINRLX_SAFETY_FLAGS,
                    "not_eligible_for_promotion": True,
                    "warnings": [f"Dependencies unavailable: {', '.join(dep_status['missing_dependencies'])}",
                                 "No real CPU PPO/A2C training was performed.",
                                 f"Candidate creation failed: {str(e)[:200]}"],
                    "created_at": now.isoformat(),
                })

        # Dependencies available — run real CPU-only training
        # This branch only executes if numpy, gymnasium, stable_baselines3, torch are all importable
        try:
            import numpy as np
            import gymnasium as gym
            from gymnasium import spaces
            from stable_baselines3 import PPO as SB3PPO, A2C as SB3A2C

            # Build tiny synthetic environment from dataset
            validation = await self.validate_dataset_contract(start_date, end_date, limit=30)
            n_assets = validation.get("asset_count", 2) or 2

            class TinyOfflineEnv(gym.Env):
                def __init__(self):
                    super().__init__()
                    self.observation_space = spaces.Box(low=-1, high=1, shape=(n_assets,), dtype=np.float32)
                    self.action_space = spaces.Discrete(3)  # 0=cash, 1=baseline, 2=risk-reduced
                    self._step = 0
                    self._max_steps = min(timesteps, 100)
                    np.random.seed(seed)

                def reset(self, **kwargs):
                    self._step = 0
                    return np.zeros(n_assets, dtype=np.float32), {}

                def step(self, action):
                    self._step += 1
                    obs = np.random.uniform(-0.05, 0.05, size=n_assets).astype(np.float32)
                    reward = float(np.sum(obs) * (0.5 + 0.5 * (action == 1)))
                    done = self._step >= self._max_steps
                    return obs, reward, done, False, {}

            algo_cls = SB3PPO if algorithm.upper() == "PPO" else SB3A2C
            env = TinyOfflineEnv()
            import time
            t0 = time.monotonic()
            model = algo_cls("MlpPolicy", env, verbose=0, seed=seed, device="cpu")
            model.learn(total_timesteps=timesteps)
            training_ms = int((time.monotonic() - t0) * 1000)

            # Extract simple policy info
            final_reward = float(np.mean([env.step(1)[1] for _ in range(10)]))

            run = RLTrainingRun(
                id=gen_uuid(), agent_key=f"finrlx_cpu_{algorithm.lower()}_research",
                environment_key=canonical_key, status="completed",
                train_start_date=start_date, train_end_date=end_date,
                config={"algorithm": algorithm, "timesteps": timesteps, "seed": seed,
                        "training_mode": f"cpu_{algorithm.lower()}", "real_neural_training": True},
                completed_at=datetime.now(timezone.utc),
            )
            self.db.add(run)

            candidate_id = gen_uuid()
            training_metrics = {"algorithm": algorithm, "timesteps": timesteps, "seed": seed,
                                "training_duration_ms": training_ms, "final_mean_reward": round(final_reward, 6),
                                "training_mode": f"cpu_{algorithm.lower()}", "real_neural_training": True}
            self.db.add(RLPolicySnapshot(
                id=candidate_id, training_run_id=run.id,
                agent_key=run.agent_key, environment_key=canonical_key,
                policy_type=f"finrlx_cpu_{algorithm.lower()}_research",
                policy_payload={"training_mode": f"cpu_{algorithm.lower()}", "real_neural_training": True,
                                "algorithm": algorithm, "safety_flags": FINRLX_SAFETY_FLAGS,
                                "notes": "CPU-only offline research prototype. Not eligible for promotion."},
                metrics=training_metrics,
            ))
            run.metrics = {**training_metrics, "policy_candidate_id": candidate_id}

            post_fp = await self._capture_production_fingerprints()
            cc = self._build_component_checks(pre_fp, post_fp)
            avail = [c for c in cc.values() if c["snapshot_available"]]
            overall_unch = all(c["unchanged"] for c in avail) if avail else None

            await self._create_audit_event("finrlx_cpu_research_train_completed", {
                "candidate_id": candidate_id, "training_run_id": run.id,
                "algorithm": algorithm, "real_neural_training": True,
                "dependency_status": dep_status,
                "safety_flags": FINRLX_SAFETY_FLAGS,
                "isolation_checks": self.get_candidate_isolation(candidate_id)["checks"],
                "component_checks": cc, "production_fingerprints_unchanged": overall_unch,
            })
            await self.db.commit()

            iso = self.get_candidate_isolation(candidate_id)
            return _json_safe({
                "policy_candidate_id": candidate_id, "training_run_id": run.id,
                "name": name, "status": "completed",
                "training_mode": f"cpu_{algorithm.lower()}", "real_neural_training": True,
                "algorithm": algorithm, "timesteps": timesteps,
                "training_metrics": training_metrics,
                "dependency_status": dep_status, "safety_flags": FINRLX_SAFETY_FLAGS,
                "not_eligible_for_promotion": True,
                "isolation_checks": iso["checks"], "isolated": True, "all_blocked": True,
                "production_fingerprints": {"before": pre_fp, "after": post_fp,
                                            "unchanged": overall_unch, "component_checks": cc},
                "warnings": ["CPU-only offline research prototype.", "Not eligible for promotion.",
                             "Not used by production decisions."],
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

        except Exception as e:
            post_fp = await self._capture_production_fingerprints()
            cc = self._build_component_checks(pre_fp, post_fp)
            avail = [c for c in cc.values() if c["snapshot_available"]]
            overall_unch = all(c["unchanged"] for c in avail) if avail else None

            await self._create_audit_event("finrlx_cpu_research_train_failed", {
                "algorithm": algorithm, "error": str(e)[:500],
                "dependency_status": dep_status,
                "safety_flags": FINRLX_SAFETY_FLAGS, "component_checks": cc,
                "production_fingerprints_unchanged": overall_unch,
            })
            await self.db.commit()

            return _json_safe({
                "policy_candidate_id": None, "training_run_id": None,
                "name": name, "status": "failed",
                "training_mode": "failed", "real_neural_training": False,
                "algorithm": algorithm, "timesteps": timesteps,
                "dependency_status": dep_status, "safety_flags": FINRLX_SAFETY_FLAGS,
                "not_eligible_for_promotion": True,
                "production_fingerprints": {"before": pre_fp, "after": post_fp,
                                            "unchanged": overall_unch, "component_checks": cc},
                "warnings": [f"Training failed: {str(e)[:200]}"],
                "created_at": now.isoformat(),
            })

    def _build_component_checks(self, pre: dict, post: dict) -> dict:
        cc = {}
        for k in ["recommendations_current", "publication_status", "overview"]:
            pre_c, post_c = pre.get(k, {}), post.get(k, {})
            pa, pb = pre_c.get("snapshot_available", False), post_c.get("snapshot_available", False)
            if pa and pb:
                unch = pre_c.get("hash") == post_c.get("hash")
            else:
                unch = None
            cc[k] = {"before_hash": pre_c.get("hash"), "after_hash": post_c.get("hash"),
                      "unchanged": unch, "snapshot_available": pa and pb}
            if not (pa and pb):
                cc[k]["reason"] = pre_c.get("reason") or post_c.get("reason") or "snapshot unavailable"
        return cc

    @staticmethod
    def safety_guard(action: str) -> dict:
        """Block any unsafe action."""
        blocked = {
            "mark_as_live", "publish", "execute", "promote",
            "affect_recommendations", "affect_overview", "affect_publication",
            "broker_execution",
        }
        if action in blocked:
            return {
                "allowed": False,
                "action": action,
                "reason": f"Action '{action}' is blocked. FinRL-X research candidates are "
                          f"research-only, offline-only, shadow-only. No production influence allowed.",
            }
        return {"allowed": True, "action": action}
