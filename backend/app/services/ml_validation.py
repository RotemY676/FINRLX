"""ML model validation service.

Phase 6B: evaluates shadow ML predictions against realized returns.

Methodology:
  - For each model_prediction, find realized return from market_bars
  - Compute directional accuracy, MAE, rank correlation, hit rate
  - Compare against deterministic engine scores
  - Produce promotion readiness assessment
"""
import math
from datetime import datetime, date, timezone, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.modeling import ModelPrediction, ModelRun, ModelDefinition, ModelValidationReport
from app.models.ingestion import MarketBar
from app.models.signal import SignalRun, SignalOutput
from app.models.base import gen_uuid

MIN_SAMPLE_FOR_REVIEW = 20
MIN_ACCURACY_FOR_REVIEW = 0.52


class MLValidationService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_realized_return(self, asset_id: str, as_of: date, horizon_days: int) -> float | None:
        """Get realized forward return from market_bars."""
        target_date = as_of + timedelta(days=horizon_days)
        start_price = (await self.db.execute(
            select(MarketBar.close)
            .where(MarketBar.asset_id == asset_id)
            .where(MarketBar.bar_date <= as_of)
            .order_by(MarketBar.bar_date.desc()).limit(1)
        )).scalar()
        end_price = (await self.db.execute(
            select(MarketBar.close)
            .where(MarketBar.asset_id == asset_id)
            .where(MarketBar.bar_date <= target_date)
            .order_by(MarketBar.bar_date.desc()).limit(1)
        )).scalar()
        if start_price and end_price and start_price > 0:
            return (end_price - start_price) / start_price
        return None

    async def _get_deterministic_scores(self, asset_id: str) -> dict[str, float]:
        """Get latest deterministic engine scores for an asset."""
        from app.models.engine import EngineDefinition
        det_keys = (await self.db.execute(
            select(EngineDefinition.key)
            .where(EngineDefinition.is_active == True)  # noqa: E712
            .where(EngineDefinition.category != "ml")
        )).scalars().all()

        scores = {}
        for key in det_keys:
            run = (await self.db.execute(
                select(SignalRun.id)
                .where(SignalRun.engine_name == key)
                .where(SignalRun.status == "completed")
                .order_by(SignalRun.run_completed_at.desc()).limit(1)
            )).scalar()
            if run:
                output = (await self.db.execute(
                    select(SignalOutput.score)
                    .where(SignalOutput.signal_run_id == run)
                    .where(SignalOutput.asset_id == asset_id)
                )).scalar()
                if output is not None:
                    scores[key] = output
        return scores

    async def evaluate_shadow_model(
        self, model_key: str = "ml_return_forecaster", horizon_days: int = 20,
    ) -> ModelValidationReport:
        """Evaluate ML predictions against realized returns."""
        now = datetime.now(timezone.utc)

        # Get latest completed predict run
        pred_run = (await self.db.execute(
            select(ModelRun)
            .where(ModelRun.model_key == model_key)
            .where(ModelRun.run_type == "predict")
            .where(ModelRun.status == "completed")
            .order_by(ModelRun.completed_at.desc()).limit(1)
        )).scalar_one_or_none()

        if not pred_run:
            report = ModelValidationReport(
                id=gen_uuid(), model_key=model_key, model_version="v1",
                evaluated_at=now, horizon_days=horizon_days,
                sample_count=0, status="failed",
                promotion_readiness="not_ready",
                warnings=["No completed prediction run found"],
            )
            self.db.add(report)
            await self.db.commit()
            return report

        preds = (await self.db.execute(
            select(ModelPrediction).where(ModelPrediction.model_run_id == pred_run.id)
        )).scalars().all()

        if not preds:
            report = ModelValidationReport(
                id=gen_uuid(), model_key=model_key, model_version="v1",
                evaluated_at=now, horizon_days=horizon_days,
                sample_count=0, status="failed",
                promotion_readiness="not_ready",
                warnings=["No predictions to evaluate"],
            )
            self.db.add(report)
            await self.db.commit()
            return report

        # Evaluate each prediction
        correct_dir = 0
        total_evaluated = 0
        abs_errors = []
        pred_vals = []
        real_vals = []
        confidences = []
        warnings = []

        # Confidence buckets: low (<0.3), medium (0.3-0.6), high (>0.6)
        buckets = {"low": {"correct": 0, "total": 0}, "medium": {"correct": 0, "total": 0}, "high": {"correct": 0, "total": 0}}

        # Deterministic engine comparison
        det_correct = {}
        det_total = {}

        for p in preds:
            realized = await self._get_realized_return(p.asset_id, p.as_of, horizon_days)
            if realized is None:
                continue

            pred_val = p.prediction_value or 0
            total_evaluated += 1
            pred_vals.append(pred_val)
            real_vals.append(realized)
            abs_errors.append(abs(pred_val - realized))
            confidences.append(p.confidence or 0)

            pred_dir = 1 if pred_val > 0 else -1
            real_dir = 1 if realized > 0 else -1
            if pred_dir == real_dir:
                correct_dir += 1

            # Confidence bucket
            conf = p.confidence or 0
            bucket = "low" if conf < 0.3 else "medium" if conf < 0.6 else "high"
            buckets[bucket]["total"] += 1
            if pred_dir == real_dir:
                buckets[bucket]["correct"] += 1

            # Compare with deterministic engines
            det_scores = await self._get_deterministic_scores(p.asset_id)
            for eng_key, eng_score in det_scores.items():
                if eng_key not in det_correct:
                    det_correct[eng_key] = 0
                    det_total[eng_key] = 0
                det_total[eng_key] += 1
                eng_dir = 1 if eng_score > 0 else -1
                if eng_dir == real_dir:
                    det_correct[eng_key] += 1

        if total_evaluated == 0:
            report = ModelValidationReport(
                id=gen_uuid(), model_key=model_key, model_version="v1",
                evaluated_at=now, horizon_days=horizon_days,
                sample_count=0, status="partial",
                promotion_readiness="needs_more_data",
                warnings=["No realized returns available for evaluation period"],
            )
            self.db.add(report)
            await self.db.commit()
            return report

        dir_accuracy = round(correct_dir / total_evaluated, 4)
        mae = round(sum(abs_errors) / len(abs_errors), 6) if abs_errors else None
        avg_conf = round(sum(confidences) / len(confidences), 4) if confidences else None

        # Rank correlation (Pearson on values — simple approximation)
        rank_corr = None
        if len(pred_vals) >= 5:
            n = len(pred_vals)
            mean_p = sum(pred_vals) / n
            mean_r = sum(real_vals) / n
            cov = sum((pred_vals[i] - mean_p) * (real_vals[i] - mean_r) for i in range(n)) / n
            std_p = math.sqrt(sum((x - mean_p) ** 2 for x in pred_vals) / n)
            std_r = math.sqrt(sum((x - mean_r) ** 2 for x in real_vals) / n)
            if std_p > 0 and std_r > 0:
                rank_corr = round(cov / (std_p * std_r), 4)

        # Calibration error: compare bucket accuracy vs avg confidence
        cal_error = None
        bucket_data = {}
        for bname, bdata in buckets.items():
            if bdata["total"] > 0:
                acc = bdata["correct"] / bdata["total"]
                bucket_data[bname] = {"accuracy": round(acc, 3), "count": bdata["total"]}

        if bucket_data:
            # Simple calibration: average |accuracy - expected_accuracy| across buckets
            errors = []
            for bname, bd in bucket_data.items():
                expected = {"low": 0.5, "medium": 0.55, "high": 0.6}.get(bname, 0.5)
                errors.append(abs(bd["accuracy"] - expected))
            cal_error = round(sum(errors) / len(errors), 4) if errors else None

        # Baseline comparison
        baseline = {}
        for eng_key in det_correct:
            if det_total[eng_key] > 0:
                baseline[eng_key] = {
                    "directional_accuracy": round(det_correct[eng_key] / det_total[eng_key], 4),
                    "sample_count": det_total[eng_key],
                }

        # Promotion readiness
        if total_evaluated < MIN_SAMPLE_FOR_REVIEW:
            readiness = "needs_more_data"
            warnings.append(f"Sample count {total_evaluated} < {MIN_SAMPLE_FOR_REVIEW} minimum")
        elif dir_accuracy >= MIN_ACCURACY_FOR_REVIEW:
            readiness = "promising_shadow" if dir_accuracy < 0.58 else "eligible_for_review"
        else:
            readiness = "not_ready"
            warnings.append(f"Directional accuracy {dir_accuracy:.1%} < {MIN_ACCURACY_FOR_REVIEW:.0%} threshold")

        status = "completed" if total_evaluated >= 5 else "partial"

        report = ModelValidationReport(
            id=gen_uuid(), model_key=model_key, model_version="v1",
            evaluated_at=now, horizon_days=horizon_days,
            sample_count=total_evaluated, status=status,
            directional_accuracy=dir_accuracy,
            mean_absolute_error=mae,
            rank_correlation=rank_corr,
            hit_rate=dir_accuracy,
            avg_confidence=avg_conf,
            calibration_error=cal_error,
            baseline_comparison=baseline if baseline else None,
            confidence_buckets=bucket_data if bucket_data else None,
            promotion_readiness=readiness,
            warnings=warnings if warnings else None,
        )
        self.db.add(report)
        await self.db.commit()
        return report

    async def get_latest_report(self, model_key: str) -> ModelValidationReport | None:
        return (await self.db.execute(
            select(ModelValidationReport)
            .where(ModelValidationReport.model_key == model_key)
            .order_by(ModelValidationReport.evaluated_at.desc()).limit(1)
        )).scalar_one_or_none()

    async def get_history(self, model_key: str) -> list[ModelValidationReport]:
        return list((await self.db.execute(
            select(ModelValidationReport)
            .where(ModelValidationReport.model_key == model_key)
            .order_by(ModelValidationReport.evaluated_at.desc()).limit(20)
        )).scalars().all())
