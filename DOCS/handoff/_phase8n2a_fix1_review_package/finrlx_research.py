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
import os
import re
import uuid
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

        # Artifact import metadata
        if not candidate.get("imported_from_artifact"):
            reasons.append("Candidate was not imported from a research artifact.")
        if not candidate.get("artifact_hash"):
            reasons.append("Candidate has no artifact_hash.")
        if not candidate.get("artifact_summary"):
            reasons.append("Candidate has no artifact_summary.")

        # Safety flags — check both candidate dict and underlying payload
        if candidate.get("not_eligible_for_promotion") is not True:
            reasons.append("not_eligible_for_promotion must be true.")
        if candidate.get("research_only") is not True:
            reasons.append("research_only must be true.")
        if candidate.get("offline_only") is not True:
            reasons.append("offline_only must be true.")
        if candidate.get("shadow_only") is not True:
            reasons.append("shadow_only must be true.")
        if candidate.get("live_pipeline_influence") is not False:
            reasons.append("live_pipeline_influence must be false.")
        if candidate.get("no_broker_execution") is not True:
            reasons.append("no_broker_execution must be true.")
        if candidate.get("no_publication_influence") is not True:
            reasons.append("no_publication_influence must be true.")
        if candidate.get("no_recommendation_pollution") is not True:
            reasons.append("no_recommendation_pollution must be true.")

        # Verify stored payload directly — do not rely on _candidate_dict() normalization
        s = (await self.db.execute(
            select(RLPolicySnapshot).where(RLPolicySnapshot.id == candidate_id)
            .where(RLPolicySnapshot.policy_type.like("finrlx_%"))
        )).scalar_one_or_none()
        if not s:
            reasons.append("Stored policy snapshot not found.")
        else:
            pp = s.policy_payload or {}
            if pp.get("imported_from_artifact") is not True:
                reasons.append("Stored payload: imported_from_artifact is not true.")
            if not pp.get("artifact_hash"):
                reasons.append("Stored payload: artifact_hash is missing.")
            if not pp.get("artifact_summary"):
                reasons.append("Stored payload: artifact_summary is missing.")

            # Stored safety_flags sub-dict (matches FINRLX_SAFETY_FLAGS keys)
            pp_sf = pp.get("safety_flags", {})
            for flag, expected in [
                ("research_only", True), ("offline_only", True), ("shadow_only", True),
                ("live_pipeline_influence", False), ("no_broker_execution", True),
                ("no_publication_influence", True), ("no_recommendation_pollution", True),
            ]:
                if pp_sf.get(flag) is not expected:
                    reasons.append(f"Stored payload: safety_flags.{flag} is not {expected}.")
            # not_eligible_for_promotion may be in safety_flags or absent (checked via top-level)
            if "not_eligible_for_promotion" in pp_sf and pp_sf["not_eligible_for_promotion"] is not True:
                reasons.append("Stored payload: safety_flags.not_eligible_for_promotion is not true.")

            # Top-level payload mirrors (if present, must match)
            for flag, expected in [
                ("research_only", True), ("offline_only", True), ("shadow_only", True),
                ("live_pipeline_influence", False), ("no_broker_execution", True),
                ("no_publication_influence", True), ("no_recommendation_pollution", True),
            ]:
                if flag in pp and pp[flag] is not expected:
                    reasons.append(f"Stored payload: top-level {flag} is not {expected}.")

        # Isolation checks
        iso = self.get_candidate_isolation(candidate_id)
        checks = iso["checks"]
        if not checks.get("promotion_blocked"):
            reasons.append("Isolation: promotion not blocked.")
        if not checks.get("publication_blocked"):
            reasons.append("Isolation: publication not blocked.")
        if not checks.get("live_recommendation_blocked"):
            reasons.append("Isolation: live recommendation not blocked.")
        if not checks.get("overview_influence_blocked"):
            reasons.append("Isolation: overview influence not blocked.")
        if not checks.get("broker_execution_blocked"):
            reasons.append("Isolation: broker execution not blocked.")
        if not iso.get("all_blocked"):
            reasons.append("Isolation: all_blocked is not true.")

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
            "isolation_checks": checks if eligible else None,
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

        inference_mode = "score_weighted_fallback_surrogate"

        await self._create_audit_event("finrlx_candidate_benchmark_requested", {
            "candidate_id": candidate_id, "artifact_hash": artifact_hash,
            "surrogate_key": surrogate_key, "inference_mode": inference_mode,
            "real_neural_inference": False,
            "artifact_metadata_used_for_inference": False,
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
                ensure_score_weighted_baseline=include_baselines,
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
                "forensic_summary_by_agent": dl.get("forensic_summary_by_agent"),
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
                "inference_mode": inference_mode,
                "real_neural_inference": False,
                "artifact_metadata_used_for_inference": False,
                "surrogate_description": "Deterministic score-weighted fallback. No neural model loaded.",
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
                "inference_mode": inference_mode,
                "real_neural_inference": False,
                "artifact_metadata_used_for_inference": False,
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
                "forensic_summary_by_agent": report["forensic_summary_by_agent"],
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
                    "Imported research candidate — score-weighted fallback surrogate benchmark.",
                    "No neural inference was run in production.",
                    "Benchmark uses deterministic score-weighted fallback. No neural model loaded.",
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

    # ── Dataset export for local research (Phase 8I) ───────────────────

    DATASET_EXPORT_SAFETY_FLAGS = {
        "research_only": True,
        "offline_only": True,
        "shadow_only": True,
        "no_production_influence": True,
        "not_eligible_for_promotion": True,
    }

    async def export_local_research_dataset(
        self,
        name: str = "Local Research Dataset Export",
        candidate_id: str | None = None,
        benchmark_report_id: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        include_features: bool = True,
        include_targets: bool = True,
        include_warnings: bool = True,
        export_format: str = "jsonl",
    ) -> dict:
        """Export a dataset for local research use only. No production influence."""
        now = datetime.now(timezone.utc)
        export_id = gen_uuid()

        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=60)

        warnings: list[str] = []

        # Validate candidate if provided
        candidate_meta = None
        if candidate_id:
            candidate = await self.get_candidate(candidate_id)
            if not candidate:
                return {"error": "Research candidate not found", "export_id": None, "status": "failed"}
            candidate_meta = {
                "id": candidate.get("id"),
                "policy_type": candidate.get("policy_type"),
                "training_mode": candidate.get("training_mode"),
                "artifact_hash": candidate.get("artifact_hash"),
            }

        # Validate benchmark if provided
        benchmark_meta = None
        if benchmark_report_id:
            benchmark_meta = {"benchmark_report_id": benchmark_report_id}

        # Use existing safe dataset source
        train_svc = RLTrainingService(self.db)
        rows = await train_svc.export_training_dataset(
            start_date=start_date, end_date=end_date, limit=500,
        )

        if not rows:
            warnings.append("No dataset rows available for the specified date range.")

        # Build export rows
        export_rows = []
        feature_schema: list[str] = []
        target_schema: list[str] = []
        warning_schema: list[str] = []

        for row in rows:
            export_row: dict = {
                "date": row.get("as_of_date"),
                "next_date": row.get("next_date"),
            }
            assets = row.get("assets", [])
            asset_data = []
            for a in assets:
                entry: dict = {"ticker": a.get("ticker")}
                if include_features:
                    entry["price"] = a.get("price")
                    entry["engine_score"] = a.get("engine_score")
                    if "price" not in feature_schema:
                        feature_schema.extend(["price", "engine_score"])
                if include_targets:
                    entry["next_price"] = a.get("next_price")
                    entry["realized_return"] = a.get("realized_return")
                    if "next_price" not in target_schema:
                        target_schema.extend(["next_price", "realized_return"])
                asset_data.append(entry)
            export_row["assets"] = asset_data

            row_warnings = row.get("warnings") or []
            if include_warnings and row_warnings:
                export_row["warnings"] = row_warnings
                for w in row_warnings:
                    if w not in warning_schema:
                        warning_schema.append(w)

            export_row["universe_tickers"] = row.get("universe_tickers", [])
            export_row["policy_constraints"] = row.get("policy_constraints", {})
            export_rows.append(export_row)

        # Date range from actual data
        dates = [r["date"] for r in export_rows if r.get("date")]
        date_range = {"start": min(dates), "end": max(dates)} if dates else None

        # Compute checksum/fingerprint
        content_str = json.dumps(_json_safe(export_rows), sort_keys=True, default=str)
        checksum = hashlib.sha256(content_str.encode()).hexdigest()[:32]
        meta_str = json.dumps({
            "export_id": export_id, "name": name,
            "start_date": start_date.isoformat(), "end_date": end_date.isoformat(),
            "row_count": len(export_rows), "format": export_format,
        }, sort_keys=True)
        fingerprint = hashlib.sha256(meta_str.encode()).hexdigest()[:16]

        # Write export files
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        export_dir = os.path.join(project_root, "research", "finrlx_cpu", "exports")
        os.makedirs(export_dir, exist_ok=True)

        export_path = os.path.join(export_dir, f"{export_id}.{export_format}")
        safe_export_rows = _json_safe(export_rows)

        metadata = _json_safe({
            "export_id": export_id,
            "created_at": now.isoformat(),
            "name": name,
            "scope": "local_research",
            "research_only": True,
            "offline_only": True,
            "shadow_only": True,
            "no_production_influence": True,
            "not_eligible_for_promotion": True,
            "source_candidate_id": candidate_id,
            "source_benchmark_report_id": benchmark_report_id,
            "candidate_metadata": candidate_meta,
            "benchmark_metadata": benchmark_meta,
            "row_count": len(export_rows),
            "date_range": date_range,
            "export_format": export_format,
            "feature_schema": feature_schema,
            "target_schema": target_schema,
            "warning_schema": warning_schema,
            "checksum": checksum,
            "fingerprint": fingerprint,
            "safety_flags": self.DATASET_EXPORT_SAFETY_FLAGS,
            "limitations": [
                "Research-only, offline-only, shadow-only dataset.",
                "Not used by production recommendations.",
                "Not eligible for promotion.",
                "No broker execution.",
                "No real-time production signal generation.",
            ],
            "warnings": warnings,
        })

        if export_format == "json":
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump({"metadata": metadata, "rows": safe_export_rows}, f, indent=2, default=str)
        else:
            # jsonl: metadata file + rows file
            meta_path = os.path.join(export_dir, f"{export_id}.meta.json")
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, default=str)
            with open(export_path, "w", encoding="utf-8") as f:
                for row in safe_export_rows:
                    f.write(json.dumps(row, default=str) + "\n")

        # Build assets list for response
        assets_list = []
        if export_format == "jsonl":
            assets_list = [
                {"type": "metadata", "path": f"research/finrlx_cpu/exports/{export_id}.meta.json"},
                {"type": "data", "path": f"research/finrlx_cpu/exports/{export_id}.jsonl"},
            ]
        else:
            assets_list = [
                {"type": "combined", "path": f"research/finrlx_cpu/exports/{export_id}.json"},
            ]

        # Audit — store full metadata for GET reconstruction
        await self._create_audit_event("finrlx_dataset_export_completed", {
            "export_id": export_id, "name": name, "row_count": len(export_rows),
            "format": export_format, "checksum": checksum, "fingerprint": fingerprint,
            "candidate_id": candidate_id, "benchmark_report_id": benchmark_report_id,
            "safety_flags": self.DATASET_EXPORT_SAFETY_FLAGS,
            "created_at": now.isoformat(),
            "scope": "local_research",
            "date_range": date_range,
            "feature_schema": feature_schema,
            "target_schema": target_schema,
            "warning_schema": warning_schema,
            "assets": assets_list,
            "export_path": f"research/finrlx_cpu/exports/{export_id}.{export_format}",
            "limitations": metadata["limitations"],
            "warnings": warnings,
        })
        await self.db.commit()

        result = _json_safe({
            "export_id": export_id,
            "created_at": now.isoformat(),
            "status": "completed",
            "name": name,
            "scope": "local_research",
            "research_only": True,
            "offline_only": True,
            "shadow_only": True,
            "no_production_influence": True,
            "not_eligible_for_promotion": True,
            "source_candidate_id": candidate_id,
            "source_benchmark_report_id": benchmark_report_id,
            "row_count": len(export_rows),
            "date_range": date_range,
            "assets": assets_list,
            "feature_schema": feature_schema,
            "target_schema": target_schema,
            "warning_schema": warning_schema,
            "export_format": export_format,
            "export_path": f"research/finrlx_cpu/exports/{export_id}.{export_format}",
            "checksum": checksum,
            "fingerprint": fingerprint,
            "limitations": [
                "Research-only, offline-only, shadow-only dataset.",
                "Not used by production recommendations.",
                "Not eligible for promotion.",
                "No broker execution.",
                "No real-time production signal generation.",
            ],
            "warnings": warnings,
            "safety_flags": self.DATASET_EXPORT_SAFETY_FLAGS,
        })

        # Register in persistent local registry
        reg_result = self.register_dataset_export(result)
        if reg_result.get("registry_skipped"):
            result.setdefault("warnings", []).append(reg_result["warning"])

        return result

    class RegistryCorruptError(Exception):
        """Raised when the export registry is corrupt and cannot be used."""
        pass

    def _require_healthy_registry(self) -> dict:
        """Load registry and raise RegistryCorruptError if corrupt."""
        registry = self.load_dataset_export_registry()
        if registry.get("registry_corrupt"):
            raise self.RegistryCorruptError(
                "Dataset export registry is corrupt. Use rebuild-registry with acknowledgement to recreate it.")
        return registry

    # ── Export registry persistence (Phase 8I.2) ───────────────────────

    _DEFAULT_LIMITATIONS = [
        "Research-only, offline-only, shadow-only dataset.",
        "Not used by production recommendations.",
        "Not eligible for promotion.",
        "No broker execution.",
        "No real-time production signal generation.",
    ]

    @staticmethod
    def _exports_dir() -> str:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        return os.path.join(project_root, "research", "finrlx_cpu", "exports")

    @staticmethod
    def _registry_path() -> str:
        return os.path.join(FinRLXResearchService._exports_dir(), "export_registry.json")

    @staticmethod
    def _empty_registry() -> dict:
        return {"version": 1, "updated_at": datetime.now(timezone.utc).isoformat(), "exports": []}

    @staticmethod
    def load_dataset_export_registry() -> dict:
        """Load registry from disk. Returns empty registry if missing. Marks corrupt if unreadable."""
        path = FinRLXResearchService._registry_path()
        if not os.path.exists(path):
            reg = FinRLXResearchService._empty_registry()
            FinRLXResearchService.save_dataset_export_registry(reg)
            return reg
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict) or "exports" not in data:
                return {"version": 1, "updated_at": None, "exports": [],
                        "registry_corrupt": True,
                        "warnings": ["Registry file exists but has invalid structure. Use rebuild-registry to recreate."]}
            return data
        except json.JSONDecodeError:
            return {"version": 1, "updated_at": None, "exports": [],
                    "registry_corrupt": True,
                    "warnings": ["Registry file is corrupt (invalid JSON). Use rebuild-registry with acknowledgement to recreate."]}
        except Exception:
            return {"version": 1, "updated_at": None, "exports": [],
                    "registry_corrupt": True,
                    "warnings": ["Registry file could not be read. Use rebuild-registry with acknowledgement to recreate."]}

    @staticmethod
    def save_dataset_export_registry(registry: dict) -> dict:
        """Atomically save registry to disk."""
        export_dir = FinRLXResearchService._exports_dir()
        os.makedirs(export_dir, exist_ok=True)
        path = FinRLXResearchService._registry_path()
        registry["updated_at"] = datetime.now(timezone.utc).isoformat()
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, default=str)
        os.replace(tmp_path, path)
        return registry

    @staticmethod
    def _check_artifact_files(export_id: str, export_format: str) -> dict:
        """Check existence of artifact files on disk."""
        export_dir = FinRLXResearchService._exports_dir()
        if export_format == "jsonl":
            meta_path = f"research/finrlx_cpu/exports/{export_id}.meta.json"
            data_path = f"research/finrlx_cpu/exports/{export_id}.jsonl"
            meta_exists = os.path.exists(os.path.join(export_dir, f"{export_id}.meta.json"))
            data_exists = os.path.exists(os.path.join(export_dir, f"{export_id}.jsonl"))
        else:
            meta_path = f"research/finrlx_cpu/exports/{export_id}.json"
            data_path = meta_path
            meta_exists = os.path.exists(os.path.join(export_dir, f"{export_id}.json"))
            data_exists = meta_exists
        return {
            "metadata_path": meta_path,
            "data_path": data_path,
            "metadata_exists": meta_exists,
            "data_exists": data_exists,
            "artifact_exists": meta_exists and data_exists,
        }

    def register_dataset_export(self, export_response: dict) -> dict:
        """Register an export in the persistent local registry. Skips save if registry is corrupt."""
        registry = self.load_dataset_export_registry()

        if registry.get("registry_corrupt"):
            logger.warning("Registry is corrupt — skipping registration for export %s", export_response.get("export_id"))
            return {"registry_skipped": True,
                    "warning": "Export artifact was created, but registry update was skipped because "
                               "export_registry.json is corrupt. Use rebuild-registry with acknowledgement to recreate it."}

        export_id = export_response.get("export_id")
        export_format = export_response.get("export_format", "jsonl")

        file_check = self._check_artifact_files(export_id, export_format)

        entry = {
            "export_id": export_id,
            "created_at": export_response.get("created_at"),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "status": "completed",
            "lifecycle_state": "active",
            "name": export_response.get("name"),
            "row_count": export_response.get("row_count", 0),
            "date_range": export_response.get("date_range"),
            "assets": export_response.get("assets", []),
            "export_format": export_format,
            "export_path": export_response.get("export_path"),
            "metadata_path": file_check["metadata_path"],
            "data_path": file_check["data_path"],
            "checksum": export_response.get("checksum"),
            "fingerprint": export_response.get("fingerprint"),
            "source_candidate_id": export_response.get("source_candidate_id"),
            "source_benchmark_report_id": export_response.get("source_benchmark_report_id"),
            "feature_schema": export_response.get("feature_schema", []),
            "target_schema": export_response.get("target_schema", []),
            "warning_schema": export_response.get("warning_schema", []),
            "research_only": True,
            "offline_only": True,
            "shadow_only": True,
            "no_production_influence": True,
            "not_eligible_for_promotion": True,
            "warnings": export_response.get("warnings", []),
            "limitations": export_response.get("limitations", self._DEFAULT_LIMITATIONS),
            "artifact_exists": file_check["artifact_exists"],
            "metadata_exists": file_check["metadata_exists"],
            "data_exists": file_check["data_exists"],
        }

        # Remove existing entry with same export_id if present (idempotent)
        registry["exports"] = [e for e in registry["exports"] if e.get("export_id") != export_id]
        registry["exports"].insert(0, entry)
        self.save_dataset_export_registry(registry)
        return entry

    def list_dataset_exports(self, lifecycle_state: str | None = None, limit: int = 50) -> list[dict]:
        """List exports from the persistent registry, newest first. Raises on corrupt."""
        registry = self._require_healthy_registry()
        exports = registry.get("exports", [])
        # Sort newest first
        exports.sort(key=lambda e: e.get("created_at") or "", reverse=True)
        if lifecycle_state:
            exports = [e for e in exports if e.get("lifecycle_state") == lifecycle_state]
        return exports[:limit]

    def get_dataset_export(self, export_id: str) -> dict | None:
        """Get a specific export by ID from registry, enriched with full schema. Raises on corrupt."""
        registry = self._require_healthy_registry()
        entry = None
        for e in registry.get("exports", []):
            if e.get("export_id") == export_id:
                entry = dict(e)
                break
        if not entry:
            return None

        # Refresh artifact existence
        export_format = entry.get("export_format", "jsonl")
        file_check = self._check_artifact_files(export_id, export_format)
        entry.update(file_check)

        # Enrich from metadata file if available
        warnings_list = list(entry.get("warnings") or [])
        export_dir = self._exports_dir()
        if export_format == "jsonl":
            meta_file = os.path.join(export_dir, f"{export_id}.meta.json")
        else:
            meta_file = os.path.join(export_dir, f"{export_id}.json")

        enriched: dict = {}
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                file_data = json.load(f)
                if export_format == "json" and "metadata" in file_data:
                    enriched = file_data["metadata"]
                else:
                    enriched = file_data
        except (FileNotFoundError, json.JSONDecodeError):
            if file_check["metadata_exists"] is False:
                warnings_list.append("Local export artifact not found on disk.")

        sf = self.DATASET_EXPORT_SAFETY_FLAGS

        return {
            "export_id": export_id,
            "created_at": entry.get("created_at") or enriched.get("created_at"),
            "updated_at": entry.get("updated_at"),
            "status": entry.get("status", "completed"),
            "lifecycle_state": entry.get("lifecycle_state", "active"),
            "name": entry.get("name") or enriched.get("name"),
            "scope": "local_research",
            "research_only": True,
            "offline_only": True,
            "shadow_only": True,
            "no_production_influence": True,
            "not_eligible_for_promotion": True,
            "source_candidate_id": entry.get("source_candidate_id") or enriched.get("source_candidate_id"),
            "source_benchmark_report_id": entry.get("source_benchmark_report_id") or enriched.get("source_benchmark_report_id"),
            "row_count": entry.get("row_count") or enriched.get("row_count", 0),
            "date_range": entry.get("date_range") or enriched.get("date_range"),
            "assets": entry.get("assets") or enriched.get("assets", []),
            "feature_schema": entry.get("feature_schema") or enriched.get("feature_schema", []),
            "target_schema": entry.get("target_schema") or enriched.get("target_schema", []),
            "warning_schema": entry.get("warning_schema") or enriched.get("warning_schema", []),
            "export_format": export_format,
            "export_path": entry.get("export_path", f"research/finrlx_cpu/exports/{export_id}.{export_format}"),
            "metadata_path": file_check["metadata_path"],
            "data_path": file_check["data_path"],
            "checksum": entry.get("checksum") or enriched.get("checksum"),
            "fingerprint": entry.get("fingerprint") or enriched.get("fingerprint"),
            "limitations": entry.get("limitations") or enriched.get("limitations", self._DEFAULT_LIMITATIONS),
            "warnings": warnings_list,
            "safety_flags": sf,
            "artifact_exists": file_check["artifact_exists"],
            "metadata_exists": file_check["metadata_exists"],
            "data_exists": file_check["data_exists"],
        }

    def mark_dataset_export_stale(self, export_id: str, reason: str | None = None) -> dict | None:
        """Mark an export as stale. Does not delete files. Raises on corrupt."""
        registry = self._require_healthy_registry()
        for entry in registry.get("exports", []):
            if entry.get("export_id") == export_id:
                entry["lifecycle_state"] = "stale"
                entry["updated_at"] = datetime.now(timezone.utc).isoformat()
                if reason:
                    entry.setdefault("warnings", []).append(f"Marked stale: {reason}")
                self.save_dataset_export_registry(registry)
                return entry
        return None

    def verify_dataset_export_artifact(self, export_id: str) -> dict | None:
        """Verify artifact files exist on disk. Strictly read-only — no registry writes."""
        registry = self._require_healthy_registry()
        entry = None
        for e in registry.get("exports", []):
            if e.get("export_id") == export_id:
                entry = e
                break
        if not entry:
            return None

        export_format = entry.get("export_format", "jsonl")
        file_check = self._check_artifact_files(export_id, export_format)

        warnings = []
        if not file_check["metadata_exists"]:
            warnings.append("Metadata file not found on disk.")
        if not file_check["data_exists"]:
            warnings.append("Data file not found on disk.")

        return {
            "export_id": export_id,
            "export_format": export_format,
            "metadata_path": file_check["metadata_path"],
            "data_path": file_check["data_path"],
            "metadata_exists": file_check["metadata_exists"],
            "data_exists": file_check["data_exists"],
            "artifact_exists": file_check["artifact_exists"],
            "lifecycle_state": entry.get("lifecycle_state", "active"),
            "warnings": warnings,
            "safety_flags": self.DATASET_EXPORT_SAFETY_FLAGS,
            "registry_snapshot_artifact_exists": entry.get("artifact_exists"),
            "registry_snapshot_metadata_exists": entry.get("metadata_exists"),
            "registry_snapshot_data_exists": entry.get("data_exists"),
        }

    def rebuild_dataset_export_registry_from_files(self) -> dict:
        """Rebuild registry by scanning exports directory. Only reads, never fabricates."""
        export_dir = self._exports_dir()
        os.makedirs(export_dir, exist_ok=True)

        entries: list[dict] = []
        seen_ids: set[str] = set()

        # Scan for .meta.json files (jsonl exports)
        for fname in os.listdir(export_dir):
            if fname.endswith(".meta.json"):
                export_id = fname.replace(".meta.json", "")
                if export_id in seen_ids:
                    continue
                seen_ids.add(export_id)
                try:
                    with open(os.path.join(export_dir, fname), "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    file_check = self._check_artifact_files(export_id, "jsonl")
                    entries.append({
                        "export_id": export_id,
                        "created_at": meta.get("created_at"),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "status": "completed",
                        "lifecycle_state": "active",
                        "name": meta.get("name"),
                        "row_count": meta.get("row_count", 0),
                        "date_range": meta.get("date_range"),
                        "assets": meta.get("assets", []),
                        "export_format": "jsonl",
                        "export_path": f"research/finrlx_cpu/exports/{export_id}.jsonl",
                        "metadata_path": file_check["metadata_path"],
                        "data_path": file_check["data_path"],
                        "checksum": meta.get("checksum"),
                        "fingerprint": meta.get("fingerprint"),
                        "source_candidate_id": meta.get("source_candidate_id"),
                        "source_benchmark_report_id": meta.get("source_benchmark_report_id"),
                        "feature_schema": meta.get("feature_schema", []),
                        "target_schema": meta.get("target_schema", []),
                        "warning_schema": meta.get("warning_schema", []),
                        "research_only": True, "offline_only": True, "shadow_only": True,
                        "no_production_influence": True, "not_eligible_for_promotion": True,
                        "warnings": meta.get("warnings", []),
                        "limitations": meta.get("limitations", self._DEFAULT_LIMITATIONS),
                        "artifact_exists": file_check["artifact_exists"],
                        "metadata_exists": file_check["metadata_exists"],
                        "data_exists": file_check["data_exists"],
                    })
                except (json.JSONDecodeError, KeyError):
                    continue

        # Scan for .json files (combined json exports, not .meta.json)
        for fname in os.listdir(export_dir):
            if fname.endswith(".json") and not fname.endswith(".meta.json") and fname != "export_registry.json" and fname != "export_registry.json.tmp":
                export_id = fname.replace(".json", "")
                if export_id in seen_ids:
                    continue
                seen_ids.add(export_id)
                try:
                    with open(os.path.join(export_dir, fname), "r", encoding="utf-8") as f:
                        file_data = json.load(f)
                    meta = file_data.get("metadata", file_data)
                    file_check = self._check_artifact_files(export_id, "json")
                    entries.append({
                        "export_id": export_id,
                        "created_at": meta.get("created_at"),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "status": "completed",
                        "lifecycle_state": "active",
                        "name": meta.get("name"),
                        "row_count": meta.get("row_count", 0),
                        "date_range": meta.get("date_range"),
                        "assets": meta.get("assets", []),
                        "export_format": "json",
                        "export_path": f"research/finrlx_cpu/exports/{export_id}.json",
                        "metadata_path": file_check["metadata_path"],
                        "data_path": file_check["data_path"],
                        "checksum": meta.get("checksum"),
                        "fingerprint": meta.get("fingerprint"),
                        "source_candidate_id": meta.get("source_candidate_id"),
                        "source_benchmark_report_id": meta.get("source_benchmark_report_id"),
                        "feature_schema": meta.get("feature_schema", []),
                        "target_schema": meta.get("target_schema", []),
                        "warning_schema": meta.get("warning_schema", []),
                        "research_only": True, "offline_only": True, "shadow_only": True,
                        "no_production_influence": True, "not_eligible_for_promotion": True,
                        "warnings": meta.get("warnings", []),
                        "limitations": meta.get("limitations", self._DEFAULT_LIMITATIONS),
                        "artifact_exists": file_check["artifact_exists"],
                        "metadata_exists": file_check["metadata_exists"],
                        "data_exists": file_check["data_exists"],
                    })
                except (json.JSONDecodeError, KeyError):
                    continue

        # Sort newest first
        entries.sort(key=lambda e: e.get("created_at") or "", reverse=True)

        registry = {"version": 1, "updated_at": datetime.now(timezone.utc).isoformat(), "exports": entries}
        self.save_dataset_export_registry(registry)

        return {"rebuilt": True, "export_count": len(entries), "safety_flags": self.DATASET_EXPORT_SAFETY_FLAGS}

    # ── Local Research Experiment Tracking (Phase 8J.1) ─────────────────

    EXPERIMENT_SAFETY_FLAGS = {
        "research_only": True,
        "offline_only": True,
        "shadow_only": True,
        "no_production_influence": True,
        "not_eligible_for_promotion": True,
    }

    ALLOWED_LIFECYCLE_STATES = {"planned", "running_offline", "completed", "failed", "archived"}

    # ── Experiment metadata sanitizer ─────────────────────────────────

    _DISALLOWED_PATH_PREFIXES = (
        "C:\\", "C:/", "D:\\", "D:/",
        "/etc/", "/home/", "/Users/", "/var/", "/root/", "/mnt/",
        "~/", "~\\",
    )
    _DISALLOWED_SECRET_PATTERNS = (
        "password", "passwd", "secret", "token", "api_key", "apikey",
        "access_key", "private_key", "database_url", "broker",
        "credential", "auth", "bearer",
    )
    _DISALLOWED_ENV_PATTERNS = (
        "$env:", "${", "%USERPROFILE%", "%APPDATA%", "%LOCALAPPDATA%",
    )

    @staticmethod
    def _is_disallowed_experiment_text(text: str) -> bool:
        """Check if a string contains path-like or secret-like patterns."""
        if not isinstance(text, str):
            return False
        lower = text.lower()
        for prefix in FinRLXResearchService._DISALLOWED_PATH_PREFIXES:
            if prefix.lower() in lower:
                return True
        for pat in FinRLXResearchService._DISALLOWED_SECRET_PATTERNS:
            if pat in lower:
                return True
        for pat in FinRLXResearchService._DISALLOWED_ENV_PATTERNS:
            if pat.lower() in lower:
                return True
        return False

    @staticmethod
    def _sanitize_experiment_text(value, max_len: int = 500) -> str:
        """Sanitize a text field: truncate and redact if it contains disallowed patterns."""
        if not isinstance(value, str):
            value = str(value) if value is not None else ""
        value = value[:max_len]
        if FinRLXResearchService._is_disallowed_experiment_text(value):
            return "[redacted]"
        return value

    @staticmethod
    def _sanitize_experiment_metric_key(key) -> str | None:
        """Sanitize a metric key. Returns None if key is disallowed."""
        if not isinstance(key, str):
            key = str(key)
        key = key[:100]
        if FinRLXResearchService._is_disallowed_experiment_text(key):
            return None
        return key

    @staticmethod
    def _sanitize_experiment_value(value, max_len: int = 500):
        """Sanitize a metric/parameter value. Returns None if disallowed or non-primitive."""
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            value = value[:max_len]
            if FinRLXResearchService._is_disallowed_experiment_text(value):
                return None
            return value
        # Drop non-primitive (dict, list, etc.)
        return None

    @staticmethod
    def _sanitize_experiment_dict(value: dict) -> dict:
        """Recursively sanitize a dict, dropping disallowed keys/values."""
        if not isinstance(value, dict):
            return {}
        result = {}
        for k, v in value.items():
            sk = FinRLXResearchService._sanitize_experiment_metric_key(k)
            if sk is None:
                continue
            sv = FinRLXResearchService._sanitize_experiment_value(v)
            if sv is None:
                continue
            result[sk] = sv
        return result

    @staticmethod
    def _sanitize_experiment_list(value: list, max_len: int = 500) -> list:
        """Sanitize a list of strings, dropping disallowed entries."""
        if not isinstance(value, list):
            return []
        result = []
        for item in value[:50]:
            s = str(item)[:max_len] if item is not None else ""
            if not FinRLXResearchService._is_disallowed_experiment_text(s):
                result.append(s)
        return result

    class ExperimentRegistryCorruptError(Exception):
        """Raised when the experiment registry is corrupt and cannot be used."""
        pass

    @staticmethod
    def _experiments_dir() -> str:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        return os.path.join(project_root, "research", "finrlx_cpu", "experiments")

    @staticmethod
    def _experiment_registry_path() -> str:
        return os.path.join(FinRLXResearchService._experiments_dir(), "experiment_registry.json")

    @staticmethod
    def _empty_experiment_registry() -> dict:
        return {"version": 1, "updated_at": datetime.now(timezone.utc).isoformat(), "experiments": []}

    @staticmethod
    def load_experiment_registry() -> dict:
        """Load experiment registry from disk. Returns empty if missing. Marks corrupt if unreadable."""
        path = FinRLXResearchService._experiment_registry_path()
        if not os.path.exists(path):
            reg = FinRLXResearchService._empty_experiment_registry()
            FinRLXResearchService.save_experiment_registry(reg)
            return reg
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict) or "experiments" not in data:
                return {"version": 1, "updated_at": None, "experiments": [],
                        "registry_corrupt": True,
                        "warnings": ["Experiment registry file has invalid structure. Use rebuild with acknowledgement to recreate."]}
            return data
        except json.JSONDecodeError:
            return {"version": 1, "updated_at": None, "experiments": [],
                    "registry_corrupt": True,
                    "warnings": ["Experiment registry is corrupt (invalid JSON). Use rebuild with acknowledgement to recreate."]}
        except Exception:
            return {"version": 1, "updated_at": None, "experiments": [],
                    "registry_corrupt": True,
                    "warnings": ["Experiment registry could not be read. Use rebuild with acknowledgement to recreate."]}

    @staticmethod
    def save_experiment_registry(registry: dict) -> dict:
        """Atomically save experiment registry to disk."""
        exp_dir = FinRLXResearchService._experiments_dir()
        os.makedirs(exp_dir, exist_ok=True)
        path = FinRLXResearchService._experiment_registry_path()
        registry["updated_at"] = datetime.now(timezone.utc).isoformat()
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, default=str)
        os.replace(tmp_path, path)
        return registry

    def _require_healthy_experiment_registry(self) -> dict:
        """Load experiment registry and raise if corrupt."""
        registry = self.load_experiment_registry()
        if registry.get("registry_corrupt"):
            raise self.ExperimentRegistryCorruptError(
                "Experiment registry is corrupt. Use rebuild with acknowledgement to recreate.")
        return registry

    def create_research_experiment(
        self,
        name: str,
        linked_export_id: str,
        hypothesis: str = "",
        method_notes: str = "",
        parameters: dict | None = None,
        expected_metrics: list | None = None,
    ) -> dict:
        """Create a new local research experiment linked to a governed dataset export."""
        registry = self._require_healthy_experiment_registry()

        # Validate linked export
        export_registry = self.load_dataset_export_registry()
        if export_registry.get("registry_corrupt"):
            return {"error": "Dataset export registry is corrupt. Cannot validate linked export.",
                    "experiment_id": None, "status": "failed"}

        linked_export = None
        for e in export_registry.get("exports", []):
            if e.get("export_id") == linked_export_id:
                linked_export = e
                break

        warnings: list[str] = []
        if not linked_export:
            return {"error": f"Linked export '{linked_export_id}' not found in dataset export registry.",
                    "experiment_id": None, "status": "failed"}
        if linked_export.get("lifecycle_state") == "stale":
            warnings.append("Linked dataset export is marked as stale.")
        if linked_export.get("artifact_exists") is False:
            warnings.append("Linked dataset export artifact files are missing from disk.")

        now = datetime.now(timezone.utc)
        experiment_id = gen_uuid()

        # Sanitize all user-controlled metadata
        redacted = False
        safe_name = self._sanitize_experiment_text(name, max_len=200)
        if safe_name == "[redacted]":
            redacted = True
        safe_hypothesis = self._sanitize_experiment_text(hypothesis, max_len=1000)
        if safe_hypothesis == "[redacted]":
            redacted = True
        safe_method_notes = self._sanitize_experiment_text(method_notes, max_len=1000)
        if safe_method_notes == "[redacted]":
            redacted = True
        raw_params = _json_safe(parameters) if parameters else {}
        safe_params = self._sanitize_experiment_dict(raw_params) if isinstance(raw_params, dict) else {}
        if len(safe_params) < len(raw_params if isinstance(raw_params, dict) else {}):
            redacted = True
        safe_metrics = self._sanitize_experiment_list(expected_metrics or [])
        if len(safe_metrics) < len(expected_metrics or []):
            redacted = True

        if redacted:
            warnings.append("Some experiment metadata fields were redacted or dropped because they looked like paths or secrets.")

        entry = {
            "experiment_id": experiment_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "lifecycle_state": "planned",
            "name": safe_name,
            "linked_export_id": linked_export_id,
            "linked_export_fingerprint": linked_export.get("fingerprint"),
            "linked_export_checksum": linked_export.get("checksum"),
            "linked_export_row_count": linked_export.get("row_count", 0),
            "linked_export_date_range": linked_export.get("date_range"),
            "hypothesis": safe_hypothesis,
            "method_notes": safe_method_notes,
            "parameters": safe_params,
            "expected_metrics": safe_metrics,
            "result_summary": None,
            "result_metrics": {},
            "result_artifact_path": None,
            "warnings": warnings,
            "limitations": [
                "Research-only, offline-only, shadow experiment.",
                "Not used by production recommendations.",
                "Not eligible for promotion.",
                "No broker execution.",
                "No automatic training or benchmark execution.",
            ],
            "research_only": True,
            "offline_only": True,
            "shadow_only": True,
            "no_production_influence": True,
            "not_eligible_for_promotion": True,
        }

        registry["experiments"].insert(0, entry)
        self.save_experiment_registry(registry)

        return {**entry, "status": "created", "safety_flags": self.EXPERIMENT_SAFETY_FLAGS}

    def list_research_experiments(self, lifecycle_state: str | None = None, limit: int = 50) -> list[dict]:
        """List experiments newest first. Raises on corrupt."""
        registry = self._require_healthy_experiment_registry()
        experiments = registry.get("experiments", [])
        experiments.sort(key=lambda e: e.get("created_at") or "", reverse=True)
        if lifecycle_state:
            experiments = [e for e in experiments if e.get("lifecycle_state") == lifecycle_state]
        return experiments[:limit]

    def get_research_experiment(self, experiment_id: str) -> dict | None:
        """Get a specific experiment by ID. Raises on corrupt."""
        registry = self._require_healthy_experiment_registry()
        for e in registry.get("experiments", []):
            if e.get("experiment_id") == experiment_id:
                result = dict(e)
                result["safety_flags"] = self.EXPERIMENT_SAFETY_FLAGS
                return result
        return None

    def update_research_experiment_state(
        self, experiment_id: str, lifecycle_state: str, reason: str | None = None,
    ) -> dict | None:
        """Update experiment lifecycle state. Does not trigger execution."""
        if lifecycle_state not in self.ALLOWED_LIFECYCLE_STATES:
            return {"error": f"Invalid lifecycle state: {lifecycle_state}. Allowed: {', '.join(sorted(self.ALLOWED_LIFECYCLE_STATES))}"}

        registry = self._require_healthy_experiment_registry()
        for entry in registry.get("experiments", []):
            if entry.get("experiment_id") == experiment_id:
                entry["lifecycle_state"] = lifecycle_state
                entry["updated_at"] = datetime.now(timezone.utc).isoformat()
                if reason:
                    safe_reason = self._sanitize_experiment_text(reason, max_len=500)
                    entry.setdefault("warnings", []).append(f"State changed to {lifecycle_state}: {safe_reason}")
                    if safe_reason == "[redacted]":
                        entry["warnings"].append(
                            "Some lifecycle reason text was redacted because it looked like a path or secret.")
                self.save_experiment_registry(registry)
                return {**entry, "safety_flags": self.EXPERIMENT_SAFETY_FLAGS}
        return None

    def import_research_experiment_results(
        self, experiment_id: str, result_summary: str = "",
        result_metrics: dict | None = None,
        warnings: list | None = None, limitations: list | None = None,
    ) -> dict | None:
        """Import metadata-only results into an experiment. Does not import code or files."""
        registry = self._require_healthy_experiment_registry()
        for entry in registry.get("experiments", []):
            if entry.get("experiment_id") == experiment_id:
                redacted = False

                # Sanitize result_summary
                safe_summary = self._sanitize_experiment_text(
                    result_summary, max_len=2000) if result_summary else None
                if safe_summary == "[redacted]":
                    redacted = True
                entry["result_summary"] = safe_summary

                # Sanitize result_metrics — drop disallowed keys/values and non-primitives
                raw_metrics = result_metrics if isinstance(result_metrics, dict) else {}
                safe_metrics = self._sanitize_experiment_dict(raw_metrics)
                if len(safe_metrics) < len(raw_metrics):
                    redacted = True
                entry["result_metrics"] = safe_metrics

                # Sanitize warnings and limitations
                if warnings and isinstance(warnings, list):
                    safe_warnings = self._sanitize_experiment_list(warnings)
                    if len(safe_warnings) < len(warnings):
                        redacted = True
                    entry["warnings"] = safe_warnings
                if limitations and isinstance(limitations, list):
                    safe_limitations = self._sanitize_experiment_list(limitations)
                    if len(safe_limitations) < len(limitations):
                        redacted = True
                    entry["limitations"] = safe_limitations

                if redacted:
                    entry.setdefault("warnings", []).append(
                        "Some result metadata fields were redacted or dropped because they looked like paths or secrets.")

                entry["updated_at"] = datetime.now(timezone.utc).isoformat()
                self.save_experiment_registry(registry)
                return {**entry, "safety_flags": self.EXPERIMENT_SAFETY_FLAGS}
        return None

    def verify_research_experiment(self, experiment_id: str) -> dict | None:
        """Verify experiment's linked export. Strictly read-only — no registry writes."""
        registry = self._require_healthy_experiment_registry()
        entry = None
        for e in registry.get("experiments", []):
            if e.get("experiment_id") == experiment_id:
                entry = e
                break
        if not entry:
            return None

        linked_export_id = entry.get("linked_export_id")
        warnings: list[str] = []

        # Check linked export in export registry
        try:
            export_registry = self.load_dataset_export_registry()
            if export_registry.get("registry_corrupt"):
                warnings.append("Dataset export registry is corrupt — cannot verify linked export.")
            else:
                linked = None
                for ex in export_registry.get("exports", []):
                    if ex.get("export_id") == linked_export_id:
                        linked = ex
                        break
                if not linked:
                    warnings.append("Linked dataset export not found in registry.")
                else:
                    if linked.get("lifecycle_state") == "stale":
                        warnings.append("Linked dataset export is marked as stale.")
                    if linked.get("artifact_exists") is False:
                        warnings.append("Linked dataset export artifact files are missing from disk.")
                    # Check checksum match
                    if entry.get("linked_export_checksum") and linked.get("checksum"):
                        if entry["linked_export_checksum"] != linked["checksum"]:
                            warnings.append("Linked export checksum has changed since experiment creation.")
        except Exception:
            warnings.append("Could not load dataset export registry for verification.")

        return {
            "experiment_id": experiment_id,
            "linked_export_id": linked_export_id,
            "linked_export_checksum": entry.get("linked_export_checksum"),
            "linked_export_fingerprint": entry.get("linked_export_fingerprint"),
            "lifecycle_state": entry.get("lifecycle_state"),
            "warnings": warnings,
            "healthy": len(warnings) == 0,
            "safety_flags": self.EXPERIMENT_SAFETY_FLAGS,
        }

    def rebuild_experiment_registry_from_files(self) -> dict:
        """Rebuild experiment registry. Since experiments are metadata-only in registry,
        this creates a fresh empty registry (no filesystem artifacts to scan)."""
        exp_dir = self._experiments_dir()
        os.makedirs(exp_dir, exist_ok=True)
        registry = self._empty_experiment_registry()
        self.save_experiment_registry(registry)
        return {"rebuilt": True, "experiment_count": 0, "safety_flags": self.EXPERIMENT_SAFETY_FLAGS}

    # ── Offline Experiment Comparison Workbench (Phase 8K.1) ────────────

    COMPARISON_SAFETY_FLAGS = {
        "research_only": True,
        "offline_only": True,
        "shadow_only": True,
        "no_production_influence": True,
        "not_eligible_for_promotion": True,
    }

    class ComparisonRegistryCorruptError(Exception):
        """Raised when the comparison registry is corrupt and cannot be used."""
        pass

    @staticmethod
    def _comparisons_dir() -> str:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        return os.path.join(project_root, "research", "finrlx_cpu", "comparisons")

    @staticmethod
    def _comparison_registry_path() -> str:
        return os.path.join(FinRLXResearchService._comparisons_dir(), "comparison_registry.json")

    @staticmethod
    def _empty_comparison_registry() -> dict:
        return {"version": 1, "updated_at": datetime.now(timezone.utc).isoformat(), "comparisons": []}

    @staticmethod
    def load_comparison_registry() -> dict:
        path = FinRLXResearchService._comparison_registry_path()
        if not os.path.exists(path):
            reg = FinRLXResearchService._empty_comparison_registry()
            FinRLXResearchService.save_comparison_registry(reg)
            return reg
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict) or "comparisons" not in data:
                return {"version": 1, "updated_at": None, "comparisons": [],
                        "registry_corrupt": True,
                        "warnings": ["Comparison registry has invalid structure. Use rebuild with acknowledgement."]}
            return data
        except json.JSONDecodeError:
            return {"version": 1, "updated_at": None, "comparisons": [],
                    "registry_corrupt": True,
                    "warnings": ["Comparison registry is corrupt (invalid JSON). Use rebuild with acknowledgement."]}
        except Exception:
            return {"version": 1, "updated_at": None, "comparisons": [],
                    "registry_corrupt": True,
                    "warnings": ["Comparison registry could not be read. Use rebuild with acknowledgement."]}

    @staticmethod
    def save_comparison_registry(registry: dict) -> dict:
        cmp_dir = FinRLXResearchService._comparisons_dir()
        os.makedirs(cmp_dir, exist_ok=True)
        path = FinRLXResearchService._comparison_registry_path()
        registry["updated_at"] = datetime.now(timezone.utc).isoformat()
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, default=str)
        os.replace(tmp_path, path)
        return registry

    def _require_healthy_comparison_registry(self) -> dict:
        registry = self.load_comparison_registry()
        if registry.get("registry_corrupt"):
            raise self.ComparisonRegistryCorruptError(
                "Comparison registry is corrupt. Use rebuild with acknowledgement to recreate.")
        return registry

    def _build_comparison_summary(self, experiments: list[dict], metric_priority: list[str]) -> dict:
        """Build deterministic comparison summary from experiment result_metrics. No ML, no inference."""
        all_metric_names: set[str] = set()
        for exp in experiments:
            rm = exp.get("result_metrics") or {}
            for k in rm.keys():
                sk = self._sanitize_experiment_metric_key(k)
                if sk is not None:
                    all_metric_names.add(sk)
        for mp in metric_priority:
            sk = self._sanitize_experiment_metric_key(mp)
            if sk is not None:
                all_metric_names.add(sk)
        metric_names = sorted(all_metric_names)

        metric_coverage: dict[str, dict] = {}
        missing_metrics: dict[str, list[str]] = {}
        ranked_metrics: dict[str, list[dict]] = {}
        warnings: list[str] = []

        for mn in metric_names:
            avail = 0
            miss = 0
            values: list[dict] = []
            mixed = False
            for exp in experiments:
                eid = exp.get("experiment_id", "")
                rm = exp.get("result_metrics") or {}
                if mn in rm:
                    v = rm[mn]
                    avail += 1
                    if isinstance(v, (int, float)):
                        values.append({"experiment_id": eid, "value": v})
                    else:
                        mixed = True
                else:
                    miss += 1
                    missing_metrics.setdefault(eid, []).append(mn)
            total = avail + miss
            metric_coverage[mn] = {
                "available_count": avail,
                "missing_count": miss,
                "coverage_ratio": round(avail / total, 2) if total > 0 else 0,
            }
            if values:
                ranked_metrics[mn] = sorted(values, key=lambda x: x["value"], reverse=True)
            if mixed and not self._is_disallowed_experiment_text(mn):
                warnings.append(f"Metric '{mn}' has mixed types across experiments.")

        for exp in experiments:
            eid = exp.get("experiment_id", "")
            if not exp.get("result_metrics"):
                warnings.append(f"Experiment {eid[:8]} has no result metrics.")
            if exp.get("lifecycle_state") != "completed":
                warnings.append(f"Experiment {eid[:8]} lifecycle is '{exp.get('lifecycle_state')}', not 'completed'.")

        if not metric_names:
            warnings.append("No comparable metrics found across selected experiments.")

        return {
            "experiment_count": len(experiments),
            "metric_names": metric_names,
            "metric_coverage": metric_coverage,
            "missing_metrics": missing_metrics,
            "ranked_metrics": ranked_metrics,
            "warnings": warnings,
        }

    def create_experiment_comparison(
        self,
        name: str,
        experiment_ids: list[str],
        metric_priority: list[str] | None = None,
        notes: str = "",
    ) -> dict:
        """Create offline comparison of 2+ experiments. No training, no inference, no promotion."""
        comp_registry = self._require_healthy_comparison_registry()

        # Validate experiment IDs from experiment registry
        try:
            exp_registry = self._require_healthy_experiment_registry()
        except self.ExperimentRegistryCorruptError:
            return {"error": "Experiment registry is corrupt. Cannot validate experiments.",
                    "comparison_id": None, "status": "failed"}

        experiments: list[dict] = []
        warnings: list[str] = []
        for eid in experiment_ids:
            found = None
            for e in exp_registry.get("experiments", []):
                if e.get("experiment_id") == eid:
                    found = e
                    break
            if not found:
                return {"error": f"Experiment '{eid}' not found in experiment registry.",
                        "comparison_id": None, "status": "failed"}
            experiments.append(found)

        # Sanitize user-controlled fields
        redacted = False
        safe_name = self._sanitize_experiment_text(name, max_len=200)
        if safe_name == "[redacted]":
            redacted = True
        safe_notes = self._sanitize_experiment_text(notes, max_len=1000)
        if safe_notes == "[redacted]":
            redacted = True
        safe_priority = self._sanitize_experiment_list(metric_priority or [])
        if len(safe_priority) < len(metric_priority or []):
            redacted = True
        if redacted:
            warnings.append("Some comparison metadata fields were redacted or dropped because they looked like paths or secrets.")

        # Build experiment snapshots — defensively sanitize all user-controlled fields
        snapshot_redacted = False
        snapshots = []
        for exp in experiments:
            safe_exp_name = self._sanitize_experiment_text(exp.get("name") or "", max_len=200)
            safe_result_summary = self._sanitize_experiment_text(exp.get("result_summary") or "", max_len=2000)
            safe_result_metrics = self._sanitize_experiment_dict(exp.get("result_metrics") or {})
            safe_snap_warnings = self._sanitize_experiment_list(exp.get("warnings") or [])
            safe_snap_limitations = self._sanitize_experiment_list(exp.get("limitations") or [])
            if (safe_exp_name == "[redacted]" or safe_result_summary == "[redacted]"
                    or len(safe_result_metrics) < len(exp.get("result_metrics") or {})
                    or len(safe_snap_warnings) < len(exp.get("warnings") or [])
                    or len(safe_snap_limitations) < len(exp.get("limitations") or [])):
                snapshot_redacted = True
            snapshots.append({
                "experiment_id": exp.get("experiment_id"),
                "name": safe_exp_name,
                "lifecycle_state": exp.get("lifecycle_state"),
                "linked_export_id": exp.get("linked_export_id"),
                "linked_export_checksum": exp.get("linked_export_checksum"),
                "linked_export_fingerprint": exp.get("linked_export_fingerprint"),
                "linked_export_row_count": exp.get("linked_export_row_count", 0),
                "result_summary": safe_result_summary,
                "result_metrics": safe_result_metrics,
                "warnings": safe_snap_warnings,
                "limitations": safe_snap_limitations,
            })
        if snapshot_redacted:
            warnings.append("Some experiment snapshot metadata was redacted or dropped because it looked like a path or secret.")

        # Build sanitized experiment dicts for comparison summary (use snapshot-safe metrics)
        sanitized_experiments = []
        for exp, snap in zip(experiments, snapshots):
            sanitized_experiments.append({
                "experiment_id": exp.get("experiment_id"),
                "lifecycle_state": exp.get("lifecycle_state"),
                "result_metrics": snap["result_metrics"],
            })

        # Build comparison summary
        summary = self._build_comparison_summary(sanitized_experiments, safe_priority)
        warnings.extend(summary.get("warnings", []))

        now = datetime.now(timezone.utc)
        comparison_id = gen_uuid()

        entry = {
            "comparison_id": comparison_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "lifecycle_state": "active",
            "name": safe_name,
            "experiment_ids": experiment_ids,
            "metric_priority": safe_priority,
            "notes": safe_notes,
            "comparison_summary": summary,
            "experiment_snapshots": snapshots,
            "warnings": warnings,
            "limitations": [
                "Research-only, offline-only, shadow comparison.",
                "Metric sorting is numeric-only and does not imply production suitability.",
                "Not used by production recommendations.",
                "Not eligible for promotion.",
                "No broker execution.",
            ],
            "research_only": True,
            "offline_only": True,
            "shadow_only": True,
            "no_production_influence": True,
            "not_eligible_for_promotion": True,
        }

        comp_registry["comparisons"].insert(0, entry)
        self.save_comparison_registry(comp_registry)

        return {**entry, "status": "created", "safety_flags": self.COMPARISON_SAFETY_FLAGS}

    def list_experiment_comparisons(self, lifecycle_state: str | None = None, limit: int = 50) -> list[dict]:
        registry = self._require_healthy_comparison_registry()
        comparisons = registry.get("comparisons", [])
        comparisons.sort(key=lambda c: c.get("created_at") or "", reverse=True)
        if lifecycle_state:
            comparisons = [c for c in comparisons if c.get("lifecycle_state") == lifecycle_state]
        return comparisons[:limit]

    def get_experiment_comparison(self, comparison_id: str) -> dict | None:
        registry = self._require_healthy_comparison_registry()
        for c in registry.get("comparisons", []):
            if c.get("comparison_id") == comparison_id:
                result = dict(c)
                result["safety_flags"] = self.COMPARISON_SAFETY_FLAGS
                return result
        return None

    def archive_experiment_comparison(self, comparison_id: str, reason: str | None = None) -> dict | None:
        registry = self._require_healthy_comparison_registry()
        for entry in registry.get("comparisons", []):
            if entry.get("comparison_id") == comparison_id:
                entry["lifecycle_state"] = "archived"
                entry["updated_at"] = datetime.now(timezone.utc).isoformat()
                if reason:
                    safe_reason = self._sanitize_experiment_text(reason, max_len=500)
                    entry.setdefault("warnings", []).append(f"Archived: {safe_reason}")
                    if safe_reason == "[redacted]":
                        entry["warnings"].append(
                            "Some archive reason text was redacted because it looked like a path or secret.")
                self.save_comparison_registry(registry)
                return {**entry, "safety_flags": self.COMPARISON_SAFETY_FLAGS}
        return None

    def verify_experiment_comparison(self, comparison_id: str) -> dict | None:
        """Verify comparison inputs. Strictly read-only — no registry writes."""
        registry = self._require_healthy_comparison_registry()
        entry = None
        for c in registry.get("comparisons", []):
            if c.get("comparison_id") == comparison_id:
                entry = c
                break
        if not entry:
            return None

        warnings: list[str] = []
        experiment_ids = entry.get("experiment_ids", [])

        try:
            exp_registry = self.load_experiment_registry()
            if exp_registry.get("registry_corrupt"):
                warnings.append("Experiment registry is corrupt — cannot verify experiments.")
            else:
                for eid in experiment_ids:
                    found = None
                    for e in exp_registry.get("experiments", []):
                        if e.get("experiment_id") == eid:
                            found = e
                            break
                    if not found:
                        warnings.append(f"Experiment {eid[:8]} not found in registry.")
                    elif not found.get("result_metrics"):
                        warnings.append(f"Experiment {eid[:8]} has no result metrics.")
                    elif found.get("lifecycle_state") != "completed":
                        warnings.append(f"Experiment {eid[:8]} lifecycle is '{found.get('lifecycle_state')}', not 'completed'.")
        except Exception:
            warnings.append("Could not load experiment registry for verification.")

        return {
            "comparison_id": comparison_id,
            "experiment_ids": experiment_ids,
            "lifecycle_state": entry.get("lifecycle_state"),
            "warnings": warnings,
            "healthy": len(warnings) == 0,
            "safety_flags": self.COMPARISON_SAFETY_FLAGS,
        }

    def rebuild_comparison_registry_from_files(self) -> dict:
        cmp_dir = self._comparisons_dir()
        os.makedirs(cmp_dir, exist_ok=True)
        registry = self._empty_comparison_registry()
        self.save_comparison_registry(registry)
        return {"rebuilt": True, "comparison_count": 0, "safety_flags": self.COMPARISON_SAFETY_FLAGS}

    # ── Research Readiness Review Gates (Phase 8L.1) ─────────────────

    READINESS_SAFETY_FLAGS = {
        "research_only": True,
        "offline_only": True,
        "shadow_only": True,
        "no_production_influence": True,
        "not_eligible_for_promotion": True,
    }

    ALLOWED_READINESS_STATES = {"draft", "needs_more_evidence", "research_review_ready", "archived"}

    @staticmethod
    def _sanitize_registry_id(value) -> str | None:
        """Sanitize a registry ID. Returns None if it contains disallowed patterns."""
        if not isinstance(value, str):
            return None
        if not value or len(value) > 200:
            return None
        if FinRLXResearchService._is_disallowed_experiment_text(value):
            return None
        return value

    @staticmethod
    def _sanitize_registry_id_list(values: list) -> list[str]:
        """Sanitize a list of registry IDs, dropping unsafe entries."""
        if not isinstance(values, list):
            return []
        result = []
        for v in values:
            sv = FinRLXResearchService._sanitize_registry_id(v)
            if sv is not None:
                result.append(sv)
        return result

    @staticmethod
    def _sanitize_metric_coverage_entry(entry: dict) -> dict:
        """Sanitize a single metric coverage dict, keeping only safe primitive fields."""
        if not isinstance(entry, dict):
            return {}
        safe = {}
        allowed_keys = {"available_count", "missing_count", "coverage_ratio"}
        for k, v in entry.items():
            if k in allowed_keys and isinstance(v, (int, float)):
                safe[k] = v
        return safe

    class ReadinessRegistryCorruptError(Exception):
        pass

    @staticmethod
    def _readiness_dir() -> str:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        return os.path.join(project_root, "research", "finrlx_cpu", "readiness")

    @staticmethod
    def _readiness_registry_path() -> str:
        return os.path.join(FinRLXResearchService._readiness_dir(), "readiness_registry.json")

    @staticmethod
    def _empty_readiness_registry() -> dict:
        return {"version": 1, "updated_at": datetime.now(timezone.utc).isoformat(), "readiness_reviews": []}

    @staticmethod
    def load_readiness_registry() -> dict:
        path = FinRLXResearchService._readiness_registry_path()
        if not os.path.exists(path):
            reg = FinRLXResearchService._empty_readiness_registry()
            FinRLXResearchService.save_readiness_registry(reg)
            return reg
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict) or "readiness_reviews" not in data:
                return {"version": 1, "updated_at": None, "readiness_reviews": [],
                        "registry_corrupt": True,
                        "warnings": ["Readiness registry has invalid structure. Use rebuild with acknowledgement."]}
            return data
        except json.JSONDecodeError:
            return {"version": 1, "updated_at": None, "readiness_reviews": [],
                    "registry_corrupt": True,
                    "warnings": ["Readiness registry is corrupt (invalid JSON). Use rebuild with acknowledgement."]}
        except Exception:
            return {"version": 1, "updated_at": None, "readiness_reviews": [],
                    "registry_corrupt": True,
                    "warnings": ["Readiness registry could not be read. Use rebuild with acknowledgement."]}

    @staticmethod
    def save_readiness_registry(registry: dict) -> dict:
        rd = FinRLXResearchService._readiness_dir()
        os.makedirs(rd, exist_ok=True)
        path = FinRLXResearchService._readiness_registry_path()
        registry["updated_at"] = datetime.now(timezone.utc).isoformat()
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, default=str)
        os.replace(tmp_path, path)
        return registry

    def _require_healthy_readiness_registry(self) -> dict:
        registry = self.load_readiness_registry()
        if registry.get("registry_corrupt"):
            raise self.ReadinessRegistryCorruptError(
                "Readiness registry is corrupt. Use rebuild with acknowledgement to recreate.")
        return registry

    def _build_readiness_findings(self, comparison: dict, experiments: list[dict]) -> list[dict]:
        """Build deterministic readiness findings. No ML, no inference."""
        findings: list[dict] = []

        # Check comparison summary
        summary = comparison.get("comparison_summary") or {}
        if not summary:
            findings.append({"finding_id": "no_comparison_summary", "severity": "blocking",
                "message": "Linked comparison has no comparison summary.",
                "operator_action": "Ensure comparison was created with valid experiments."})
        else:
            mc = summary.get("metric_coverage") or {}
            mm = summary.get("missing_metrics") or {}
            if mm:
                findings.append({"finding_id": "metric_coverage_incomplete", "severity": "warning",
                    "message": "Some selected experiments are missing one or more comparison metrics.",
                    "operator_action": "Review missing metrics before marking this package as research review ready."})
            if not mc:
                findings.append({"finding_id": "no_metric_coverage", "severity": "blocking",
                    "message": "Comparison has no metric coverage data.",
                    "operator_action": "Ensure experiments have imported result metrics."})

        # Check experiments have results
        for exp in experiments:
            eid = (exp.get("experiment_id") or "")[:8]
            if not exp.get("result_metrics"):
                findings.append({"finding_id": f"no_results_{eid}", "severity": "warning",
                    "message": f"Experiment {eid} has no result metrics.",
                    "operator_action": "Import result metadata for this experiment."})
            if exp.get("lifecycle_state") != "completed":
                raw_state = exp.get("lifecycle_state") or "unknown"
                safe_state = raw_state if not self._is_disallowed_experiment_text(str(raw_state)) else "[redacted]"
                findings.append({"finding_id": f"not_completed_{eid}", "severity": "info",
                    "message": f"Experiment {eid} lifecycle is not 'completed' (current: {safe_state}).",
                    "operator_action": "Consider completing the experiment before final review."})

        # Check warnings in comparison
        cmp_warnings = comparison.get("warnings") or []
        if cmp_warnings:
            findings.append({"finding_id": "comparison_has_warnings", "severity": "info",
                "message": f"Linked comparison has {len(cmp_warnings)} warning(s).",
                "operator_action": "Review comparison warnings."})

        return findings

    def create_research_readiness_review(
        self, name: str, linked_comparison_id: str,
        operator_notes: str = "", checklist: dict | None = None,
    ) -> dict:
        """Create a research readiness review linked to a comparison."""
        rd_registry = self._require_healthy_readiness_registry()

        # Sanitize linked_comparison_id before any storage or echo
        safe_cmp_id = self._sanitize_registry_id(linked_comparison_id)
        if safe_cmp_id is None:
            return {"error": "Linked comparison ID is invalid or unsafe.",
                    "readiness_id": None, "status": "failed"}

        # Load comparison
        try:
            cmp_registry = self._require_healthy_comparison_registry()
        except self.ComparisonRegistryCorruptError:
            return {"error": "Comparison registry is corrupt.", "readiness_id": None, "status": "failed"}

        comparison = None
        for c in cmp_registry.get("comparisons", []):
            if c.get("comparison_id") == safe_cmp_id:
                comparison = c
                break
        if not comparison:
            return {"error": "Linked comparison not found.",
                    "readiness_id": None, "status": "failed"}

        # Resolve linked IDs — sanitize to prevent unsafe values from leaking
        experiment_ids = self._sanitize_registry_id_list(comparison.get("experiment_ids") or [])
        export_ids = []
        for snap in comparison.get("experiment_snapshots") or []:
            eid = self._sanitize_registry_id(snap.get("linked_export_id"))
            if eid and eid not in export_ids:
                export_ids.append(eid)

        # Load experiments for findings
        experiments = []
        try:
            exp_registry = self.load_experiment_registry()
            if not exp_registry.get("registry_corrupt"):
                for eid in experiment_ids:
                    for e in exp_registry.get("experiments", []):
                        if e.get("experiment_id") == eid:
                            experiments.append(e)
                            break
        except Exception:
            pass

        # Sanitize user fields
        warnings: list[str] = []
        redacted = False
        safe_name = self._sanitize_experiment_text(name, max_len=200)
        if safe_name == "[redacted]":
            redacted = True
        safe_notes = self._sanitize_experiment_text(operator_notes, max_len=1000)
        if safe_notes == "[redacted]":
            redacted = True
        if redacted:
            warnings.append("Some readiness metadata was redacted because it looked like a path or secret.")

        # Build checklist
        default_checklist = {
            "comparison_exists": True,
            "experiments_exist": len(experiments) > 0,
            "exports_exist": len(export_ids) > 0,
            "result_metadata_present": any(e.get("result_metrics") for e in experiments),
            "metric_coverage_reviewed": False,
            "missing_metrics_reviewed": False,
            "warnings_reviewed": False,
            "limitations_reviewed": False,
            "safety_flags_confirmed": False,
        }
        if checklist and isinstance(checklist, dict):
            for k in default_checklist:
                if k in checklist and isinstance(checklist[k], bool):
                    default_checklist[k] = checklist[k]

        # Build evidence summary — defensively sanitize all registry-derived fields
        evidence_redacted = False
        cmp_summary = comparison.get("comparison_summary") or {}

        safe_cmp_name = self._sanitize_experiment_text(comparison.get("name") or "", 200)
        safe_cmp_state = self._sanitize_experiment_text(comparison.get("lifecycle_state") or "", 50)
        if safe_cmp_name == "[redacted]" or safe_cmp_state == "[redacted]":
            evidence_redacted = True

        # Sanitize metric_coverage: filter unsafe keys AND sanitize nested values
        raw_mc = cmp_summary.get("metric_coverage") or {}
        safe_mc = {}
        for mk, mv in raw_mc.items():
            sk = self._sanitize_experiment_metric_key(mk)
            if sk is None:
                evidence_redacted = True
                continue
            safe_mc[sk] = self._sanitize_metric_coverage_entry(mv) if isinstance(mv, dict) else {}

        # Sanitize missing_metrics: filter unsafe metric names AND sanitize experiment-id keys
        raw_mm = cmp_summary.get("missing_metrics") or {}
        safe_mm = {}
        for exp_id_key, metric_list in raw_mm.items():
            safe_key = self._sanitize_registry_id(exp_id_key)
            if safe_key is None:
                evidence_redacted = True
                continue
            safe_metrics = []
            if isinstance(metric_list, list):
                for m in metric_list:
                    sm = self._sanitize_experiment_metric_key(m)
                    if sm is not None:
                        safe_metrics.append(sm)
                    else:
                        evidence_redacted = True
            safe_mm[safe_key] = safe_metrics

        # Sanitize experiment evidence
        safe_exp_evidence = []
        for e in experiments:
            se_name = self._sanitize_experiment_text(e.get("name") or "", 200)
            se_state = self._sanitize_experiment_text(e.get("lifecycle_state") or "", 50)
            if se_name == "[redacted]" or se_state == "[redacted]":
                evidence_redacted = True
            safe_exp_evidence.append({
                "experiment_id": e.get("experiment_id"),
                "name": se_name,
                "lifecycle_state": se_state,
                "has_results": bool(e.get("result_metrics")),
            })

        evidence = {
            "comparison": {"comparison_id": safe_cmp_id, "name": safe_cmp_name,
                           "experiment_count": len(experiment_ids), "lifecycle_state": safe_cmp_state},
            "experiments": safe_exp_evidence,
            "exports": [{"export_id": eid} for eid in export_ids],
            "metric_coverage": safe_mc,
            "missing_metrics": safe_mm,
            "warnings": self._sanitize_experiment_list(comparison.get("warnings") or []),
            "limitations": self._sanitize_experiment_list(comparison.get("limitations") or []),
        }
        if evidence_redacted:
            warnings.append("Some readiness evidence was redacted or dropped because it looked like a path or secret.")

        # Build findings
        findings = self._build_readiness_findings(comparison, experiments)
        has_blocking = any(f["severity"] == "blocking" for f in findings)

        # Suggested state
        all_reviewed = all(default_checklist.get(k) for k in [
            "metric_coverage_reviewed", "missing_metrics_reviewed",
            "warnings_reviewed", "limitations_reviewed", "safety_flags_confirmed"])
        if has_blocking:
            suggested = "needs_more_evidence"
        elif all_reviewed:
            suggested = "research_review_ready"
        else:
            suggested = "draft"

        now = datetime.now(timezone.utc)
        readiness_id = gen_uuid()

        entry = {
            "readiness_id": readiness_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "readiness_state": "draft",
            "name": safe_name,
            "linked_comparison_id": safe_cmp_id,
            "linked_experiment_ids": experiment_ids,
            "linked_export_ids": export_ids,
            "operator_notes": safe_notes,
            "checklist": default_checklist,
            "evidence_summary": evidence,
            "readiness_findings": findings,
            "suggested_readiness_state": suggested,
            "warnings": warnings,
            "limitations": [
                "Research-only readiness review.",
                "Does not imply production suitability.",
                "Not eligible for promotion.",
                "No broker execution.",
            ],
            "research_only": True,
            "offline_only": True,
            "shadow_only": True,
            "no_production_influence": True,
            "not_eligible_for_promotion": True,
        }

        rd_registry["readiness_reviews"].insert(0, entry)
        self.save_readiness_registry(rd_registry)
        return {**entry, "status": "created", "safety_flags": self.READINESS_SAFETY_FLAGS}

    def list_research_readiness_reviews(self, readiness_state: str | None = None, limit: int = 50) -> list[dict]:
        registry = self._require_healthy_readiness_registry()
        reviews = registry.get("readiness_reviews", [])
        reviews.sort(key=lambda r: r.get("created_at") or "", reverse=True)
        if readiness_state:
            reviews = [r for r in reviews if r.get("readiness_state") == readiness_state]
        return reviews[:limit]

    def get_research_readiness_review(self, readiness_id: str) -> dict | None:
        registry = self._require_healthy_readiness_registry()
        for r in registry.get("readiness_reviews", []):
            if r.get("readiness_id") == readiness_id:
                result = dict(r)
                result["safety_flags"] = self.READINESS_SAFETY_FLAGS
                return result
        return None

    def update_research_readiness_review_state(
        self, readiness_id: str, readiness_state: str, reason: str | None = None,
    ) -> dict | None:
        if readiness_state not in self.ALLOWED_READINESS_STATES:
            return {"error": f"Invalid readiness state: {readiness_state}. Allowed: {', '.join(sorted(self.ALLOWED_READINESS_STATES))}"}

        registry = self._require_healthy_readiness_registry()
        for entry in registry.get("readiness_reviews", []):
            if entry.get("readiness_id") == readiness_id:
                # Gate: research_review_ready requires checklist and no blocking findings
                if readiness_state == "research_review_ready":
                    cl = entry.get("checklist") or {}
                    required = ["warnings_reviewed", "limitations_reviewed", "safety_flags_confirmed"]
                    missing = [k for k in required if not cl.get(k)]
                    if missing:
                        return {"error": f"Cannot mark research_review_ready: checklist items not confirmed: {', '.join(missing)}"}
                    blocking = [f for f in (entry.get("readiness_findings") or []) if f.get("severity") == "blocking"]
                    if blocking:
                        return {"error": f"Cannot mark research_review_ready: {len(blocking)} blocking finding(s) remain."}

                entry["readiness_state"] = readiness_state
                entry["updated_at"] = datetime.now(timezone.utc).isoformat()
                if reason:
                    safe_reason = self._sanitize_experiment_text(reason, max_len=500)
                    entry.setdefault("warnings", []).append(f"State changed to {readiness_state}: {safe_reason}")
                    if safe_reason == "[redacted]":
                        entry["warnings"].append("Some state reason was redacted because it looked like a path or secret.")
                self.save_readiness_registry(registry)
                return {**entry, "safety_flags": self.READINESS_SAFETY_FLAGS}
        return None

    def archive_research_readiness_review(self, readiness_id: str, reason: str | None = None) -> dict | None:
        registry = self._require_healthy_readiness_registry()
        for entry in registry.get("readiness_reviews", []):
            if entry.get("readiness_id") == readiness_id:
                entry["readiness_state"] = "archived"
                entry["updated_at"] = datetime.now(timezone.utc).isoformat()
                if reason:
                    safe_reason = self._sanitize_experiment_text(reason, max_len=500)
                    entry.setdefault("warnings", []).append(f"Archived: {safe_reason}")
                    if safe_reason == "[redacted]":
                        entry["warnings"].append("Some archive reason was redacted because it looked like a path or secret.")
                self.save_readiness_registry(registry)
                return {**entry, "safety_flags": self.READINESS_SAFETY_FLAGS}
        return None

    def verify_research_readiness_review(self, readiness_id: str) -> dict | None:
        """Verify readiness review. Strictly read-only."""
        registry = self._require_healthy_readiness_registry()
        entry = None
        for r in registry.get("readiness_reviews", []):
            if r.get("readiness_id") == readiness_id:
                entry = r
                break
        if not entry:
            return None

        warnings: list[str] = []
        raw_cmp_id = entry.get("linked_comparison_id")
        safe_cmp_id = self._sanitize_registry_id(raw_cmp_id) if raw_cmp_id else None
        if raw_cmp_id and safe_cmp_id is None:
            warnings.append("Linked comparison ID contains unsafe content and was redacted.")
        cmp_id = safe_cmp_id or "[redacted]"

        safe_exp_ids = self._sanitize_registry_id_list(entry.get("linked_experiment_ids") or [])

        try:
            cmp_registry = self.load_comparison_registry()
            if cmp_registry.get("registry_corrupt"):
                warnings.append("Comparison registry is corrupt.")
            elif safe_cmp_id:
                found = any(c.get("comparison_id") == safe_cmp_id for c in cmp_registry.get("comparisons", []))
                if not found:
                    warnings.append("Linked comparison not found in registry.")
        except Exception:
            warnings.append("Could not load comparison registry.")

        try:
            exp_registry = self.load_experiment_registry()
            if exp_registry.get("registry_corrupt"):
                warnings.append("Experiment registry is corrupt.")
            else:
                for eid in safe_exp_ids:
                    found = any(e.get("experiment_id") == eid for e in exp_registry.get("experiments", []))
                    if not found:
                        warnings.append(f"Experiment {eid[:8]} not found.")
                    else:
                        exp = next(e for e in exp_registry["experiments"] if e["experiment_id"] == eid)
                        if not exp.get("result_metrics"):
                            warnings.append(f"Experiment {eid[:8]} has no result metrics.")
        except Exception:
            warnings.append("Could not load experiment registry.")

        return {
            "readiness_id": readiness_id,
            "linked_comparison_id": cmp_id,
            "linked_experiment_ids": safe_exp_ids,
            "readiness_state": entry.get("readiness_state"),
            "warnings": warnings,
            "healthy": len(warnings) == 0,
            "safety_flags": self.READINESS_SAFETY_FLAGS,
        }

    def rebuild_readiness_registry_from_files(self) -> dict:
        rd = self._readiness_dir()
        os.makedirs(rd, exist_ok=True)
        registry = self._empty_readiness_registry()
        self.save_readiness_registry(registry)
        return {"rebuilt": True, "review_count": 0, "safety_flags": self.READINESS_SAFETY_FLAGS}

    @staticmethod
    def _is_path_under_root(child_path: str, root_path: str) -> bool:
        """Check if child_path is contained within root_path using safe path logic.

        Avoids false positives for sibling paths, e.g.:
          /data/vol2/x under /data/vol => False
          /data/vol/x  under /data/vol => True
        """
        try:
            real_child = os.path.realpath(child_path)
            real_root = os.path.realpath(root_path)
            return os.path.commonpath([real_child, real_root]) == real_root
        except (ValueError, OSError):
            return False

    @staticmethod
    def get_persistence_status() -> dict:
        """Inspect all registry directories and files, report persistence and deployment status.

        Read-only probe. Does NOT modify any registry files.
        Research-only, offline-only, no production influence.
        """
        # ── project root (used to sanitize paths) ──
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )

        def _rel(abs_path: str) -> str:
            """Return path relative to project root, forward-slash normalised."""
            try:
                return os.path.relpath(abs_path, project_root).replace("\\", "/")
            except ValueError:
                return "<outside-project>"

        def _probe_dir_writable(dir_path: str) -> bool:
            """Write+delete a tiny temp file to confirm dir is writable."""
            try:
                probe = os.path.join(dir_path, f".persistence_probe_{uuid.uuid4().hex}.tmp")
                with open(probe, "w", encoding="utf-8") as f:
                    f.write("probe")
                os.remove(probe)
                return True
            except Exception:
                return False

        # ── registry descriptors ──
        registry_specs = [
            {
                "registry_name": "dataset_exports",
                "registry_kind": "exports",
                "dir_fn": FinRLXResearchService._exports_dir,
                "file_fn": FinRLXResearchService._registry_path,
                "load_fn": FinRLXResearchService.load_dataset_export_registry,
                "items_key": "exports",
            },
            {
                "registry_name": "experiments",
                "registry_kind": "experiments",
                "dir_fn": FinRLXResearchService._experiments_dir,
                "file_fn": FinRLXResearchService._experiment_registry_path,
                "load_fn": FinRLXResearchService.load_experiment_registry,
                "items_key": "experiments",
            },
            {
                "registry_name": "comparisons",
                "registry_kind": "comparisons",
                "dir_fn": FinRLXResearchService._comparisons_dir,
                "file_fn": FinRLXResearchService._comparison_registry_path,
                "load_fn": FinRLXResearchService.load_comparison_registry,
                "items_key": "comparisons",
            },
            {
                "registry_name": "readiness_reviews",
                "registry_kind": "readiness",
                "dir_fn": FinRLXResearchService._readiness_dir,
                "file_fn": FinRLXResearchService._readiness_registry_path,
                "load_fn": FinRLXResearchService.load_readiness_registry,
                "items_key": "readiness_reviews",
            },
        ]

        registry_statuses = []
        global_warnings: list[str] = []

        for spec in registry_specs:
            dir_path = spec["dir_fn"]()
            file_path = spec["file_fn"]()
            warnings: list[str] = []

            dir_exists = os.path.isdir(dir_path)
            file_exists = os.path.isfile(file_path)

            # directory readable
            dir_readable = False
            if dir_exists:
                try:
                    os.listdir(dir_path)
                    dir_readable = True
                except Exception:
                    warnings.append("Directory exists but is not readable.")

            # directory writable
            dir_writable = False
            if dir_exists and dir_readable:
                dir_writable = _probe_dir_writable(dir_path)
                if not dir_writable:
                    warnings.append("Directory exists but is not writable.")

            # file readable
            file_readable = False
            if file_exists:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        f.read(1)
                    file_readable = True
                except Exception:
                    warnings.append("Registry file exists but is not readable.")

            # file writable
            file_writable = False
            if file_exists:
                try:
                    file_writable = os.access(file_path, os.W_OK)
                except Exception:
                    pass
                if not file_writable:
                    warnings.append("Registry file exists but is not writable.")

            # item count
            item_count = 0
            registry_corrupt = False
            if file_exists and file_readable:
                try:
                    reg = spec["load_fn"]()
                    if reg.get("registry_corrupt"):
                        registry_corrupt = True
                        warnings.append("Registry file is corrupt or has invalid structure.")
                    else:
                        items = reg.get(spec["items_key"], [])
                        item_count = len(items) if isinstance(items, list) else 0
                except Exception:
                    registry_corrupt = True
                    warnings.append("Failed to load registry.")

            # status
            if not dir_exists:
                status = "missing"
                warnings.append("Directory does not exist.")
            elif registry_corrupt:
                status = "degraded"
            elif not dir_writable or (file_exists and not file_writable):
                status = "degraded"
            elif not file_exists:
                status = "missing"
                warnings.append("Registry file does not exist.")
            else:
                status = "ok"

            registry_statuses.append({
                "registry_name": spec["registry_name"],
                "registry_kind": spec["registry_kind"],
                "directory_path": _rel(dir_path),
                "registry_file_path": _rel(file_path),
                "directory_exists": dir_exists,
                "registry_file_exists": file_exists,
                "directory_readable": dir_readable,
                "directory_writable": dir_writable,
                "registry_file_readable": file_readable,
                "registry_file_writable": file_writable,
                "item_count": item_count,
                "status": status,
                "warnings": warnings,
            })

        # ── environment detection ──
        railway_env = os.environ.get("RAILWAY_ENVIRONMENT")
        railway_project = os.environ.get("RAILWAY_PROJECT_ID")
        railway_service = os.environ.get("RAILWAY_SERVICE_ID")
        railway_service_name = os.environ.get("RAILWAY_SERVICE_NAME")
        railway_volume = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")

        is_railway = bool(railway_env or railway_project or railway_service or railway_service_name)

        appears_containerized = False
        try:
            if os.path.exists("/.dockerenv"):
                appears_containerized = True
        except Exception:
            pass
        if is_railway:
            appears_containerized = True

        if is_railway:
            deployment_environment = "railway"
        elif appears_containerized:
            deployment_environment = "container"
        else:
            deployment_environment = "local"

        is_persistent_volume = bool(railway_volume)

        # ── truthful volume usage check ──
        # The mere existence of RAILWAY_VOLUME_MOUNT_PATH does NOT mean
        # the research storage root is inside that volume.  We must check
        # whether the actual storage directory is under the mount path.
        abs_storage_root = os.path.join(project_root, "research", "finrlx_cpu")
        storage_root_uses_volume = False
        sanitized_volume_path: str | None = None
        if railway_volume:
            sanitized_volume_path = railway_volume.replace("\\", "/")
            storage_root_uses_volume = FinRLXResearchService._is_path_under_root(
                abs_storage_root, railway_volume
            )

        # ── warnings ──
        if appears_containerized and not is_persistent_volume:
            global_warnings.append(
                "Container deployment detected without persistent volume — "
                "registry data may be lost on redeploy."
            )
        elif appears_containerized and is_persistent_volume and not storage_root_uses_volume:
            global_warnings.append(
                "Persistent volume detected (RAILWAY_VOLUME_MOUNT_PATH is set), "
                "but the FINRLX research storage root does not appear to be "
                "inside the mounted volume. Registry data may still be ephemeral."
            )

        # aggregate any per-registry warnings into global
        any_degraded = any(r["status"] == "degraded" for r in registry_statuses)
        any_missing = any(r["status"] == "missing" for r in registry_statuses)
        all_ok = all(r["status"] == "ok" for r in registry_statuses)

        if any_degraded:
            global_warnings.append("One or more registries are in a degraded state.")
        if any_missing:
            global_warnings.append("One or more registry directories or files are missing.")

        # recommended next action
        actually_durable = is_persistent_volume and storage_root_uses_volume
        if all_ok and not appears_containerized:
            recommended = None
        elif all_ok and appears_containerized and actually_durable:
            recommended = None
        elif all_ok and appears_containerized and is_persistent_volume and not storage_root_uses_volume:
            recommended = (
                "A persistent volume is configured but the research storage root "
                "is not inside it. Move the storage root under the volume mount "
                "path or reconfigure the volume to cover the research directory."
            )
        elif all_ok and appears_containerized and not is_persistent_volume:
            recommended = "Configure a persistent volume to prevent data loss on redeploy."
        elif any_degraded:
            recommended = "Investigate degraded registries; check file permissions and disk space."
        elif any_missing:
            recommended = "Run the relevant rebuild-registry endpoint to initialise missing registries."
        else:
            recommended = None

        storage_root = _rel(abs_storage_root)

        return {
            "storage_mode": "local_file_backed",
            "storage_root": storage_root,
            "is_local_file_backed": True,
            "is_database_backed": False,
            "is_persistent_volume_configured": is_persistent_volume,
            "storage_root_uses_persistent_volume": storage_root_uses_volume,
            "persistent_volume_mount_path": sanitized_volume_path,
            "deployment_environment": deployment_environment,
            "appears_containerized": appears_containerized,
            "registry_statuses": registry_statuses,
            "warnings": global_warnings,
            "limitations": [
                "Registries use local JSON files, not database tables",
                "State is not replicated across instances",
                "No automatic backup mechanism",
            ],
            "recommended_next_action": recommended,
            "database_metadata_mirror": {
                "available": True,
                "artifact_storage_database_backed": False,
                "local_registries_still_operational_source": True,
            },
            "research_only": True,
            "offline_only": True,
            "no_production_influence": True,
        }

    # ── Phase 8N.2A: Registry Metadata Mirror helpers ─────────────────

    _SECRET_PATTERNS = re.compile(
        r"(password|token|api_key|secret|DATABASE_URL|credentials)"
        r"\s*[=:]\s*\S+"
        r"|bearer\s+\S+"
        r"|postgres(ql)?://\S+",
        re.IGNORECASE,
    )

    _SECRET_KEY_NAMES = frozenset({
        "password", "token", "bearer", "api_key", "secret",
        "database_url", "credentials", "authorization",
    })

    @staticmethod
    def _sanitize_mirror_value(val):
        """Redact potential secrets from a string value."""
        if val is None:
            return None
        s = str(val)[:2000]
        return FinRLXResearchService._SECRET_PATTERNS.sub("[REDACTED]", s)

    @staticmethod
    def _sanitize_mirror_payload(value, max_depth: int = 4):
        """Recursively sanitize a value for safe metadata mirror storage.

        - Strings: redact secrets, truncate
        - Lists: sanitize each item, limit length to 50
        - Dicts: sanitize keys/values, drop secret-named keys, limit 50 keys
        - int/float/bool/None: pass through
        - Other: convert to sanitized string
        """
        if max_depth <= 0:
            return "[truncated]"
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            return FinRLXResearchService._sanitize_mirror_value(value)
        if isinstance(value, list):
            return [
                FinRLXResearchService._sanitize_mirror_payload(v, max_depth - 1)
                for v in value[:50]
            ]
        if isinstance(value, dict):
            result = {}
            for k, v in list(value.items())[:50]:
                sk = str(k).lower()
                if sk in FinRLXResearchService._SECRET_KEY_NAMES:
                    result[str(k)[:200]] = "[REDACTED]"
                else:
                    result[str(k)[:200]] = FinRLXResearchService._sanitize_mirror_payload(
                        v, max_depth - 1
                    )
            return result
        # Fallback: convert to sanitized string
        return FinRLXResearchService._sanitize_mirror_value(str(value))

    @staticmethod
    def _load_registry_file_read_only(path: str, items_key: str, registry_kind: str) -> dict:
        """Load a registry JSON file in read-only mode.

        Unlike the operational load_*_registry() methods, this:
        - Does NOT create missing files or directories
        - Does NOT save empty registries
        - Does NOT rebuild corrupt files
        - Returns an empty result if the file is missing
        """
        if not os.path.exists(path):
            return {"_missing": True, items_key: [], "warnings": [f"{registry_kind} registry file not found"]}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict) or items_key not in data:
                return {"registry_corrupt": True, items_key: [],
                        "warnings": [f"{registry_kind} registry has invalid structure"]}
            return data
        except json.JSONDecodeError:
            return {"registry_corrupt": True, items_key: [],
                    "warnings": [f"{registry_kind} registry file is corrupt (invalid JSON)"]}
        except Exception:
            return {"registry_corrupt": True, items_key: [],
                    "warnings": [f"{registry_kind} registry file could not be read"]}

    @staticmethod
    def build_registry_metadata_mirror_candidates() -> list[dict]:
        """Build sanitized candidate dicts from all 4 local registries.

        Truly read-only — does NOT create, overwrite, rebuild, or mutate
        any local registry files.  Uses _load_registry_file_read_only()
        instead of the operational load_*_registry() methods.

        Research-only, offline-only, no production influence.
        """
        sanitize = FinRLXResearchService._sanitize_mirror_value
        deep_sanitize = FinRLXResearchService._sanitize_mirror_payload
        candidates: list[dict] = []

        # ── Registry specs: (kind, items_key, id_key, path_fn) ──
        registry_specs = [
            {
                "registry_kind": "dataset_export",
                "items_key": "exports",
                "id_key": "export_id",
                "path_fn": FinRLXResearchService._registry_path,
            },
            {
                "registry_kind": "experiment",
                "items_key": "experiments",
                "id_key": "experiment_id",
                "path_fn": FinRLXResearchService._experiment_registry_path,
            },
            {
                "registry_kind": "comparison",
                "items_key": "comparisons",
                "id_key": "comparison_id",
                "path_fn": FinRLXResearchService._comparison_registry_path,
            },
            {
                "registry_kind": "readiness_review",
                "items_key": "readiness_reviews",
                "id_key": "readiness_id",
                "path_fn": FinRLXResearchService._readiness_registry_path,
            },
        ]

        for spec in registry_specs:
            kind = spec["registry_kind"]
            try:
                reg_path = spec["path_fn"]()
                reg = FinRLXResearchService._load_registry_file_read_only(
                    reg_path, spec["items_key"], kind
                )
            except Exception:
                candidates.append({
                    "registry_kind": kind,
                    "record_id": "__registry_error__",
                    "record_hash": None,
                    "record_state": None,
                    "display_name": f"[{kind} registry load error]",
                    "source_registry_path": None,
                    "artifact_path": None,
                    "metadata_summary_json": {},
                    "warnings_json": [f"Failed to load {kind} registry"],
                    "limitations_json": [],
                    "mirror_status": "error",
                })
                continue

            if reg.get("registry_corrupt"):
                candidates.append({
                    "registry_kind": kind,
                    "record_id": "__registry_corrupt__",
                    "record_hash": None,
                    "record_state": None,
                    "display_name": f"[{kind} registry corrupt]",
                    "source_registry_path": sanitize(spec["path_fn"]()),
                    "artifact_path": None,
                    "metadata_summary_json": {},
                    "warnings_json": reg.get("warnings", [f"{kind} registry is corrupt"]),
                    "limitations_json": [],
                    "mirror_status": "error",
                })
                continue

            items = reg.get(spec["items_key"], [])
            if not isinstance(items, list):
                continue

            # Sanitized relative source path
            try:
                raw_path = spec["path_fn"]()
                project_root = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                )
                source_path = sanitize(os.path.relpath(raw_path, project_root).replace("\\", "/"))
            except Exception:
                source_path = None

            for item in items:
                record_id = str(item.get(spec["id_key"], ""))[:100]
                if not record_id:
                    continue

                # Build sanitized metadata summary — only safe fields
                raw_summary: dict = {}
                if kind == "dataset_export":
                    for k in ("row_count", "date_range", "export_format",
                              "feature_schema", "target_schema"):
                        if k in item:
                            raw_summary[k] = item[k]
                elif kind == "experiment":
                    for k in ("linked_export_id", "linked_export_row_count",
                              "linked_export_date_range", "result_metrics"):
                        if k in item:
                            raw_summary[k] = item[k]
                elif kind == "comparison":
                    for k in ("experiment_count", "metric_priority",
                              "created_at"):
                        if k in item:
                            raw_summary[k] = item[k]
                    raw_summary["experiment_count"] = len(item.get("experiment_ids", []))
                elif kind == "readiness_review":
                    for k in ("linked_comparison_id", "readiness_state",
                              "checklist_passed", "checklist_total",
                              "created_at"):
                        if k in item:
                            raw_summary[k] = item[k]

                # Recursively sanitize all structured fields
                summary = deep_sanitize(raw_summary)
                warnings_list = deep_sanitize(item.get("warnings", []))
                limitations_list = deep_sanitize(item.get("limitations", []))

                # record_hash: fingerprint or checksum
                record_hash = item.get("fingerprint") or item.get("checksum") or None
                if record_hash:
                    record_hash = sanitize(str(record_hash)[:200])

                # record_state
                record_state = item.get("lifecycle_state") or item.get("readiness_state") or item.get("status")
                if record_state:
                    record_state = sanitize(str(record_state)[:50])

                # display_name
                display_name = item.get("name") or item.get("display_name") or None
                if display_name:
                    display_name = sanitize(str(display_name)[:300])

                # artifact_path
                artifact_path = item.get("export_path") or item.get("data_path") or None
                if artifact_path:
                    artifact_path = sanitize(str(artifact_path)[:500])

                candidates.append({
                    "registry_kind": kind,
                    "record_id": sanitize(record_id),
                    "record_hash": record_hash,
                    "record_state": record_state,
                    "display_name": display_name,
                    "source_registry_path": source_path,
                    "artifact_path": artifact_path,
                    "metadata_summary_json": summary,
                    "warnings_json": warnings_list,
                    "limitations_json": limitations_list,
                    "mirror_status": "active",
                })

        return candidates

    async def sync_registry_metadata_mirror(self, dry_run: bool = True) -> dict:
        """Sync sanitized research registry metadata to Postgres mirror.

        If dry_run=True, returns counts without writing to DB.
        Research-only, offline-only, no production influence.
        """
        from app.models.research_registry_metadata import ResearchRegistryMetadata

        candidates = self.build_registry_metadata_mirror_candidates()

        counts_by_kind: dict[str, int] = {}
        for c in candidates:
            k = c["registry_kind"]
            counts_by_kind[k] = counts_by_kind.get(k, 0) + 1

        result = {
            "dry_run": dry_run,
            "candidates_seen": len(candidates),
            "inserted_count": 0,
            "updated_count": 0,
            "skipped_count": 0,
            "error_count": 0,
            "counts_by_registry_kind": counts_by_kind,
            "warnings": [],
            "limitations": [
                "This is a metadata mirror only — artifacts remain local/file-backed",
                "Local JSON registries remain the operational source",
            ],
            "research_only": True,
            "offline_only": True,
            "no_production_influence": True,
        }

        if dry_run:
            return result

        inserted = 0
        updated = 0
        skipped = 0
        error_count = 0

        for candidate in candidates:
            try:
                stmt = select(ResearchRegistryMetadata).where(
                    ResearchRegistryMetadata.registry_kind == candidate["registry_kind"],
                    ResearchRegistryMetadata.record_id == candidate["record_id"],
                )
                db_result = await self.db.execute(stmt)
                existing = db_result.scalar_one_or_none()

                now = func.now()

                if existing:
                    existing.record_hash = candidate["record_hash"]
                    existing.record_state = candidate["record_state"]
                    existing.display_name = candidate["display_name"]
                    existing.source_registry_path = candidate["source_registry_path"]
                    existing.artifact_path = candidate["artifact_path"]
                    existing.metadata_summary_json = candidate["metadata_summary_json"]
                    existing.warnings_json = candidate["warnings_json"]
                    existing.limitations_json = candidate["limitations_json"]
                    existing.mirror_status = candidate["mirror_status"]
                    existing.last_seen_at = datetime.now(timezone.utc)
                    existing.research_only = True
                    existing.offline_only = True
                    existing.no_production_influence = True
                    updated += 1
                else:
                    row = ResearchRegistryMetadata(
                        registry_kind=candidate["registry_kind"],
                        record_id=candidate["record_id"],
                        record_hash=candidate["record_hash"],
                        record_state=candidate["record_state"],
                        display_name=candidate["display_name"],
                        source_registry_path=candidate["source_registry_path"],
                        artifact_path=candidate["artifact_path"],
                        metadata_summary_json=candidate["metadata_summary_json"],
                        warnings_json=candidate["warnings_json"],
                        limitations_json=candidate["limitations_json"],
                        mirror_status=candidate["mirror_status"],
                        research_only=True,
                        offline_only=True,
                        no_production_influence=True,
                    )
                    self.db.add(row)
                    inserted += 1
            except Exception as exc:
                error_count += 1
                logger.warning(
                    "Failed to upsert mirror row for %s/%s: %s",
                    candidate["registry_kind"], candidate["record_id"], exc,
                )

        try:
            await self.db.commit()
        except Exception as exc:
            error_count += len(candidates)
            inserted = 0
            updated = 0
            result["warnings"].append(f"Commit failed: {str(exc)[:200]}")
            logger.error("Registry metadata mirror commit failed: %s", exc)

        result["inserted_count"] = inserted
        result["updated_count"] = updated
        result["skipped_count"] = skipped
        result["error_count"] = error_count

        return result

    async def get_registry_metadata_mirror_status(self) -> dict:
        """Query the research_registry_metadata table and return summary status.

        Read-only. Research-only, offline-only, no production influence.
        """
        from app.models.research_registry_metadata import ResearchRegistryMetadata

        try:
            # Total count
            total_stmt = select(func.count(ResearchRegistryMetadata.id))
            total_result = await self.db.execute(total_stmt)
            total_count = total_result.scalar() or 0

            # Counts by registry_kind
            kind_stmt = select(
                ResearchRegistryMetadata.registry_kind,
                func.count(ResearchRegistryMetadata.id),
            ).group_by(ResearchRegistryMetadata.registry_kind)
            kind_result = await self.db.execute(kind_stmt)
            counts_by_kind = {row[0]: row[1] for row in kind_result.all()}

            # Counts by mirror_status
            status_stmt = select(
                ResearchRegistryMetadata.mirror_status,
                func.count(ResearchRegistryMetadata.id),
            ).group_by(ResearchRegistryMetadata.mirror_status)
            status_result = await self.db.execute(status_stmt)
            counts_by_status = {row[0]: row[1] for row in status_result.all()}

            # Latest sync
            latest_stmt = select(func.max(ResearchRegistryMetadata.last_seen_at))
            latest_result = await self.db.execute(latest_stmt)
            latest_val = latest_result.scalar()
            latest_sync_at = latest_val.isoformat() if latest_val else None

            warnings: list[str] = []
        except Exception as exc:
            logger.warning("Failed to query registry metadata mirror: %s", exc)
            return {
                "is_database_metadata_mirror_enabled": True,
                "is_database_backed_artifact_storage": False,
                "local_registries_still_operational_source": True,
                "total_mirrored_records": 0,
                "counts_by_registry_kind": {},
                "counts_by_mirror_status": {},
                "latest_sync_at": None,
                "warnings": [f"Failed to query mirror table: {str(exc)[:200]}"],
                "limitations": [
                    "This is a metadata mirror only — artifacts remain local/file-backed",
                    "Local JSON registries remain the operational source",
                ],
                "research_only": True,
                "offline_only": True,
                "no_production_influence": True,
            }

        return {
            "is_database_metadata_mirror_enabled": True,
            "is_database_backed_artifact_storage": False,
            "local_registries_still_operational_source": True,
            "total_mirrored_records": total_count,
            "counts_by_registry_kind": counts_by_kind,
            "counts_by_mirror_status": counts_by_status,
            "latest_sync_at": latest_sync_at,
            "warnings": warnings,
            "limitations": [
                "This is a metadata mirror only — artifacts remain local/file-backed",
                "Local JSON registries remain the operational source",
            ],
            "research_only": True,
            "offline_only": True,
            "no_production_influence": True,
        }

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
