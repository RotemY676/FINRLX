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
from datetime import date, datetime, timezone, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rl import RLPolicySnapshot, RLTrainingRun
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
            .where(RLPolicySnapshot.policy_type == "finrlx_research_stub")
            .order_by(RLPolicySnapshot.created_at.desc()).limit(20)
        )).scalars().all()
        return [self._candidate_dict(s) for s in snapshots]

    async def get_candidate(self, candidate_id: str) -> dict | None:
        s = (await self.db.execute(
            select(RLPolicySnapshot).where(RLPolicySnapshot.id == candidate_id)
            .where(RLPolicySnapshot.policy_type == "finrlx_research_stub")
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
            "metrics": s.metrics,
            "created_at": s.created_at.isoformat() if s.created_at else None,
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
