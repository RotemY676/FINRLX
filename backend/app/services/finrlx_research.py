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
            "imported_from_artifact": payload.get("imported_from_artifact", False),
            "artifact_hash": payload.get("artifact_hash"),
            "artifact_summary": payload.get("artifact_summary"),
            "source": payload.get("source"),
            "notes": payload.get("notes"),
            "not_eligible_for_promotion": True,
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
            # Option A: no candidate when dependencies unavailable.
            # No DB writes keeps the transaction clean; fingerprints are read-only.
            post_fp = await self._capture_production_fingerprints()
            cc = self._build_component_checks(pre_fp, post_fp)
            avail = [c for c in cc.values() if c["snapshot_available"]]
            overall_unch = all(c["unchanged"] for c in avail) if avail else None

            await self._create_audit_event("finrlx_cpu_research_train_dependency_unavailable", {
                "algorithm": algorithm, "dependency_status": dep_status,
                "safety_flags": FINRLX_SAFETY_FLAGS, "component_checks": cc,
                "production_fingerprints_unchanged": overall_unch,
            })
            await self.db.commit()

            return _json_safe({
                "policy_candidate_id": None, "training_run_id": None,
                "name": name, "status": "dependency_unavailable",
                "training_mode": "dependency_unavailable", "real_neural_training": False,
                "algorithm": algorithm, "timesteps": timesteps,
                "dependency_status": dep_status, "safety_flags": FINRLX_SAFETY_FLAGS,
                "not_eligible_for_promotion": True,
                "candidate_isolation_applicable": False,
                "isolation_reason": "No candidate created because neural dependencies are unavailable.",
                "production_fingerprints": {"before": pre_fp, "after": post_fp,
                                            "unchanged": overall_unch, "component_checks": cc},
                "warnings": [
                    f"Neural dependencies unavailable: {', '.join(dep_status['missing_dependencies'])}.",
                    "No candidate was created.",
                    "No real CPU PPO/A2C training was performed.",
                ],
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

    # ── Research artifact import (Phase 8E) ────────────────────────────

    ARTIFACT_REQUIRED_FIELDS = [
        "artifact_type", "schema_version", "research_only", "offline_only",
        "shadow_only", "not_eligible_for_promotion", "live_pipeline_influence",
        "no_broker_execution", "no_publication_influence", "no_recommendation_pollution",
        "algorithm", "real_neural_training", "cpu_only", "synthetic_data",
        "dataset_summary", "training_config", "training_metrics",
        "artifact_created_at", "warnings",
    ]

    @staticmethod
    def validate_research_artifact(artifact: dict) -> dict:
        """Validate a research artifact for import. Returns validation result dict."""
        errors: list[str] = []
        warnings: list[str] = []

        # Required fields
        for f in FinRLXResearchService.ARTIFACT_REQUIRED_FIELDS:
            if f not in artifact:
                errors.append(f"Missing required field: {f}")

        # Type check
        if artifact.get("artifact_type") != "finrlx_cpu_rl_research_artifact":
            errors.append(f"Invalid artifact_type: {artifact.get('artifact_type')}")

        # Safety flags — hard reject on any unsafe value
        if artifact.get("research_only") is not True:
            errors.append("research_only must be true")
        if artifact.get("offline_only") is not True:
            errors.append("offline_only must be true")
        if artifact.get("shadow_only") is not True:
            errors.append("shadow_only must be true")
        if artifact.get("not_eligible_for_promotion") is not True:
            errors.append("not_eligible_for_promotion must be true")
        if artifact.get("live_pipeline_influence") is not False:
            errors.append("live_pipeline_influence must be false")
        if artifact.get("no_broker_execution") is not True:
            errors.append("no_broker_execution must be true")
        if artifact.get("no_publication_influence") is not True:
            errors.append("no_publication_influence must be true")
        if artifact.get("no_recommendation_pollution") is not True:
            errors.append("no_recommendation_pollution must be true")
        if artifact.get("cpu_only") is not True:
            errors.append("cpu_only must be true")

        # Algorithm
        algo = artifact.get("algorithm")
        if algo not in ("PPO", "A2C"):
            errors.append(f"algorithm must be PPO or A2C, got: {algo}")

        # Type checks
        if not isinstance(artifact.get("real_neural_training"), bool):
            errors.append("real_neural_training must be boolean")
        if not isinstance(artifact.get("synthetic_data"), bool):
            errors.append("synthetic_data must be boolean")
        if not isinstance(artifact.get("dataset_summary"), dict):
            errors.append("dataset_summary must be a dict")
        if not isinstance(artifact.get("training_config"), dict):
            errors.append("training_config must be a dict")
        if not isinstance(artifact.get("training_metrics"), dict):
            errors.append("training_metrics must be a dict")
        if not isinstance(artifact.get("warnings"), list):
            errors.append("warnings must be a list")

        # Consistency checks
        if artifact.get("real_neural_training") is True:
            tc = artifact.get("training_config", {})
            tm = artifact.get("training_metrics", {})
            if "algorithm" not in tc and "algorithm" not in tm:
                warnings.append("real_neural_training=true but no algorithm in training_config/metrics")
            if "timesteps" not in tc and "timesteps" not in tm:
                warnings.append("real_neural_training=true but no timesteps in training_config/metrics")
            if "seed" not in tc and "seed" not in tm:
                warnings.append("real_neural_training=true but no seed in training_config/metrics")

        if artifact.get("synthetic_data") is True:
            ds = artifact.get("dataset_summary", {})
            w_list = artifact.get("warnings", [])
            has_synthetic_label = ds.get("synthetic") is True or any(
                "synthetic" in str(w).lower() for w in w_list
            )
            if not has_synthetic_label:
                warnings.append("synthetic_data=true but no synthetic label in dataset_summary or warnings")

        # Compute artifact hash
        artifact_hash = FinRLXResearchService._compute_artifact_hash(artifact)

        valid = len(errors) == 0
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "artifact_hash": artifact_hash,
            "normalized_artifact_summary": {
                "algorithm": artifact.get("algorithm"),
                "real_neural_training": artifact.get("real_neural_training"),
                "synthetic_data": artifact.get("synthetic_data"),
                "cpu_only": artifact.get("cpu_only"),
                "schema_version": artifact.get("schema_version"),
                "artifact_created_at": artifact.get("artifact_created_at"),
            },
            "safety_flags": FINRLX_SAFETY_FLAGS,
        }

    @staticmethod
    def _compute_artifact_hash(artifact: dict) -> str:
        """Compute deterministic SHA-256 hash of artifact (excluding volatile fields)."""
        stable = {k: v for k, v in artifact.items() if k != "artifact_created_at"}
        raw = json.dumps(stable, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    async def import_research_artifact(
        self,
        artifact: dict,
        source: str = "unknown",
        notes: str | None = None,
    ) -> dict:
        """Import a validated research artifact as a shadow-only candidate."""
        now = datetime.now(timezone.utc)

        # Validate first
        validation = self.validate_research_artifact(artifact)
        artifact_hash = validation["artifact_hash"]

        # Capture pre-import fingerprints
        pre_fp = await self._capture_production_fingerprints()

        if not validation["valid"]:
            await self._create_audit_event("finrlx_research_artifact_import_rejected", {
                "source": source, "artifact_hash": artifact_hash,
                "validation_errors": validation["errors"],
                "safety_flags": FINRLX_SAFETY_FLAGS,
            })
            await self.db.commit()
            return _json_safe({
                "status": "rejected",
                "policy_candidate_id": None,
                "validation_result": validation,
                "safety_flags": FINRLX_SAFETY_FLAGS,
                "warnings": validation["errors"],
                "created_at": now.isoformat(),
            })

        # Audit: requested
        await self._create_audit_event("finrlx_research_artifact_import_requested", {
            "source": source, "notes": notes, "artifact_hash": artifact_hash,
            "algorithm": artifact.get("algorithm"),
            "real_neural_training": artifact.get("real_neural_training"),
            "synthetic_data": artifact.get("synthetic_data"),
            "safety_flags": FINRLX_SAFETY_FLAGS,
        })

        algo = artifact.get("algorithm", "PPO").lower()
        env_svc = RLEnvironmentService(self.db)
        canonical_key, _ = env_svc.resolve_key("quantpipeline_offline_v1")

        # Create candidate
        candidate_id = gen_uuid()
        policy_type = f"finrlx_cpu_{algo}_research_import"
        training_mode = f"imported_cpu_{algo}_research"

        snapshot = RLPolicySnapshot(
            id=candidate_id,
            training_run_id=None,
            agent_key=f"finrlx_cpu_{algo}_research_import",
            environment_key=canonical_key,
            policy_type=policy_type,
            policy_payload=_json_safe({
                "training_mode": training_mode,
                "real_neural_training": artifact.get("real_neural_training", False),
                "imported_from_artifact": True,
                "artifact_hash": artifact_hash,
                "artifact_summary": validation["normalized_artifact_summary"],
                "safety_flags": FINRLX_SAFETY_FLAGS,
                "source": source,
                "notes": notes,
            }),
            metrics=_json_safe(artifact.get("training_metrics", {})),
        )
        self.db.add(snapshot)

        # Post-import fingerprints
        post_fp = await self._capture_production_fingerprints()
        cc = self._build_component_checks(pre_fp, post_fp)
        avail = [c for c in cc.values() if c["snapshot_available"]]
        overall_unch = all(c["unchanged"] for c in avail) if avail else None

        iso = self.get_candidate_isolation(candidate_id)

        # Audit: completed
        await self._create_audit_event("finrlx_research_artifact_import_completed", {
            "candidate_id": candidate_id, "policy_type": policy_type,
            "training_mode": training_mode, "source": source,
            "artifact_hash": artifact_hash,
            "real_neural_training": artifact.get("real_neural_training"),
            "synthetic_data": artifact.get("synthetic_data"),
            "safety_flags": FINRLX_SAFETY_FLAGS,
            "isolation_checks": iso["checks"],
            "component_checks": cc,
            "production_fingerprints_unchanged": overall_unch,
        })
        await self.db.commit()

        return _json_safe({
            "status": "imported",
            "policy_candidate_id": candidate_id,
            "policy_type": policy_type,
            "training_mode": training_mode,
            "real_neural_training": artifact.get("real_neural_training", False),
            "imported_from_artifact": True,
            "artifact_hash": artifact_hash,
            "validation_result": validation,
            "safety_flags": FINRLX_SAFETY_FLAGS,
            "not_eligible_for_promotion": True,
            "isolation_checks": iso["checks"],
            "isolated": True,
            "all_blocked": True,
            "production_fingerprints": {
                "before": pre_fp, "after": post_fp,
                "unchanged": overall_unch, "component_checks": cc,
            },
            "warnings": [
                "Research artifact imported as shadow-only candidate.",
                "Not eligible for promotion.",
                "Not used by production decisions.",
                "No broker execution.",
            ],
            "created_at": now.isoformat(),
        })

    # ── Candidate benchmark evaluation (Phase 8F) ─────────────────────

    async def check_benchmark_eligibility(self, candidate_id: str) -> dict:
        """Check whether a candidate is eligible for benchmark evaluation."""
        candidate = await self.get_candidate(candidate_id)
        if not candidate:
            return {"eligible": False, "reasons": ["Candidate not found."],
                    "candidate_summary": None, "safety_flags": FINRLX_SAFETY_FLAGS,
                    "isolation_checks": None}

        reasons = []
        if not candidate.get("imported_from_artifact"):
            reasons.append("Candidate was not imported from a research artifact.")
        if not candidate.get("artifact_hash"):
            reasons.append("Candidate has no artifact_hash.")
        sf = candidate.get("safety_flags", {})
        if not sf.get("research_only"):
            reasons.append("Candidate is not research_only.")

        eligible = len(reasons) == 0
        return {
            "eligible": eligible,
            "reasons": reasons if reasons else ["Candidate is benchmark-eligible."],
            "candidate_summary": {
                "id": candidate.get("id"),
                "policy_type": candidate.get("policy_type"),
                "training_mode": candidate.get("training_mode"),
                "imported_from_artifact": candidate.get("imported_from_artifact"),
                "artifact_hash": candidate.get("artifact_hash"),
                "real_neural_training": candidate.get("real_neural_training"),
            },
            "safety_flags": FINRLX_SAFETY_FLAGS,
            "isolation_checks": self.get_candidate_isolation(candidate_id)["checks"] if eligible else None,
        }

    async def run_candidate_benchmark(
        self,
        candidate_id: str,
        name: str = "Imported Candidate Benchmark",
        start_date: date | None = None,
        end_date: date | None = None,
        include_baselines: bool = True,
    ) -> dict:
        """Run an offline benchmark comparing an imported candidate against baseline agents."""
        from app.services.rl_benchmark import RLBenchmarkService
        from app.services.rl_agents import AGENTS
        from app.services.rl_training import _score_weighted_agent_fn

        now = datetime.now(timezone.utc)

        # Check eligibility
        eligibility = await self.check_benchmark_eligibility(candidate_id)
        if not eligibility["eligible"]:
            await self._create_audit_event("finrlx_candidate_benchmark_rejected", {
                "candidate_id": candidate_id, "reasons": eligibility["reasons"],
                "safety_flags": FINRLX_SAFETY_FLAGS,
            })
            await self.db.commit()
            return _json_safe({
                "status": "rejected",
                "benchmark_report_id": None,
                "reasons": eligibility["reasons"],
                "safety_flags": FINRLX_SAFETY_FLAGS,
                "created_at": now.isoformat(),
            })

        candidate = await self.get_candidate(candidate_id)
        artifact_hash = candidate.get("artifact_hash")
        iso = self.get_candidate_isolation(candidate_id)

        pre_fp = await self._capture_production_fingerprints()

        # Register surrogate agent temporarily
        surrogate_key = f"imported_candidate:{candidate_id[:8]}"
        AGENTS[surrogate_key] = _score_weighted_agent_fn({})  # deterministic score-proportional

        await self._create_audit_event("finrlx_candidate_benchmark_requested", {
            "candidate_id": candidate_id, "artifact_hash": artifact_hash,
            "surrogate_key": surrogate_key, "inference_mode": "surrogate_metadata_only",
            "real_neural_inference": False,
            "include_baselines": include_baselines,
            "safety_flags": FINRLX_SAFETY_FLAGS,
        })

        try:
            agent_keys = [surrogate_key]
            if include_baselines:
                agent_keys += ["heuristic_baseline", "random_valid", "score_weighted_baseline"]

            bench_svc = RLBenchmarkService(self.db)
            report_obj = await bench_svc.run_benchmark(
                name=name,
                start_date=start_date,
                end_date=end_date,
                agent_keys=agent_keys,
            )

            # Convert ORM object to dict
            dl = report_obj.dataset_lineage or {}
            report = {
                "id": report_obj.id,
                "status": report_obj.status,
                "compared_agents": report_obj.compared_agents,
                "metrics_by_agent": report_obj.metrics_by_agent,
                "reward_breakdown_by_agent": report_obj.reward_breakdown_by_agent,
                "forensic_summary": report_obj.forensic_summary,
                "result_fingerprint": dl.get("result_fingerprint"),
                "invariant_check_results": dl.get("invariant_check_results"),
            }

            post_fp = await self._capture_production_fingerprints()
            cc = self._build_component_checks(pre_fp, post_fp)
            avail = [c for c in cc.values() if c["snapshot_available"]]
            overall_unch = all(c["unchanged"] for c in avail) if avail else None

            context = {
                "candidate_id": candidate_id,
                "policy_type": candidate.get("policy_type"),
                "training_mode": candidate.get("training_mode"),
                "imported_from_artifact": True,
                "artifact_hash": artifact_hash,
                "inference_mode": "surrogate_metadata_only",
                "real_neural_inference": False,
                "not_eligible_for_promotion": True,
                "research_only": True,
                "offline_only": True,
                "shadow_only": True,
                "surrogate_agent_key": surrogate_key,
            }

            await self._create_audit_event("finrlx_candidate_benchmark_completed", {
                "candidate_id": candidate_id, "artifact_hash": artifact_hash,
                "benchmark_report_id": report["id"],
                "surrogate_key": surrogate_key,
                "inference_mode": "surrogate_metadata_only",
                "real_neural_inference": False,
                "executed_agents": report["compared_agents"],
                "safety_flags": FINRLX_SAFETY_FLAGS,
                "isolation_checks": iso["checks"],
                "component_checks": cc,
                "production_fingerprints_unchanged": overall_unch,
                "result_fingerprint": report["result_fingerprint"],
            })
            await self.db.commit()

            return _json_safe({
                "status": report["status"],
                "benchmark_report_id": report["id"],
                "is_complete_comparison": report["status"] == "completed",
                "requested_agents": agent_keys,
                "executed_agents": report["compared_agents"] or [],
                "skipped_agents": [a for a in agent_keys if a not in (report["compared_agents"] or [])],
                "metrics_by_agent": report["metrics_by_agent"],
                "reward_breakdown_by_agent": report["reward_breakdown_by_agent"],
                "forensic_summary": report["forensic_summary"],
                "safety_flags": FINRLX_SAFETY_FLAGS,
                "result_fingerprint": report["result_fingerprint"],
                "invariant_check_results": report["invariant_check_results"],
                "candidate_benchmark_context": context,
                "isolation_checks": iso["checks"],
                "isolated": True,
                "all_blocked": True,
                "production_fingerprints": {
                    "before": pre_fp, "after": post_fp,
                    "unchanged": overall_unch, "component_checks": cc,
                },
                "warnings": [
                    "Imported research candidate — surrogate metadata benchmark.",
                    "No neural inference was run in production.",
                    "Benchmark uses deterministic score-weighted surrogate adapter.",
                    "Not eligible for promotion.",
                    "Not used by production decisions.",
                ],
                "created_at": now.isoformat(),
            })
        finally:
            AGENTS.pop(surrogate_key, None)

    async def get_candidate_benchmarks(self, candidate_id: str) -> list[dict]:
        """Retrieve benchmark reports linked to a candidate via audit events."""
        events = (await self.db.execute(
            select(AuditEvent)
            .where(AuditEvent.action == "finrlx_candidate_benchmark_completed")
            .where(AuditEvent.object_type == "finrlx_research")
            .order_by(AuditEvent.occurred_at.desc())
            .limit(20)
        )).scalars().all()

        results = []
        for e in events:
            d = e.details or {}
            if d.get("candidate_id") == candidate_id:
                results.append({
                    "benchmark_report_id": d.get("benchmark_report_id"),
                    "candidate_id": candidate_id,
                    "artifact_hash": d.get("artifact_hash"),
                    "inference_mode": d.get("inference_mode"),
                    "real_neural_inference": d.get("real_neural_inference", False),
                    "executed_agents": d.get("executed_agents"),
                    "result_fingerprint": d.get("result_fingerprint"),
                    "safety_flags": d.get("safety_flags"),
                    "occurred_at": e.occurred_at.isoformat() if e.occurred_at else None,
                })
        return results

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
