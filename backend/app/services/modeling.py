"""ML model registry and baseline model service.

Phase 6A: lightweight baseline ML model — no external ML dependencies.

Baseline model: ml_return_forecaster
  - Reads feature_values (return_5d/20d/60d, volatility, sentiment, etc.)
  - Computes a weighted linear score toward expected forward return
  - Calibrates confidence from feature completeness
  - This is explicitly a baseline — not advanced ML

No scikit-learn, no numpy, no network calls.
"""
import math
from datetime import date, datetime, timezone, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.modeling import ModelDefinition, ModelRun, ModelPrediction
from app.models.feature import FeatureSet, FeatureValue
from app.models.reference import Asset
from app.models.base import gen_uuid


FEATURE_KEYS = [
    "return_5d", "return_20d", "return_60d",
    "volatility_20d", "drawdown_20d", "relative_volume_20d",
    "news_sentiment_7d", "news_count_7d",
]

DEFAULT_MODELS = [
    {
        "key": "ml_return_forecaster",
        "name": "Baseline Return Forecaster",
        "category": "ml",
        "description": "Lightweight baseline linear scoring model for forward return estimation. "
                       "NOT advanced ML — uses weighted feature combination with no training optimization.",
        "model_type": "baseline_linear",
        "target": "forward_return_20d",
        "feature_keys": FEATURE_KEYS,
        "prediction_horizon_days": 20,
        "version": "v1",
        "status": "experimental",
        "is_shadow": True,
    },
]

# Baseline model weights (manually calibrated, not learned)
BASELINE_WEIGHTS = {
    "return_5d": 0.10,
    "return_20d": 0.25,
    "return_60d": 0.20,
    "volatility_20d": -0.15,   # higher vol → lower expected return
    "drawdown_20d": 0.10,      # deeper drawdown (negative) → lower score
    "relative_volume_20d": 0.05,
    "news_sentiment_7d": 0.10,
    "news_count_7d": 0.05,
}


def _baseline_predict(features: dict[str, tuple[float | None, str]]) -> dict:
    """Compute baseline linear prediction from features.

    Score = sum(weight_i * normalized_feature_i) for features with quality=ok.
    Confidence = proportion of ok features × base_confidence.
    """
    score = 0.0
    ok_count = 0
    total = len(FEATURE_KEYS)
    drivers = []

    for key in FEATURE_KEYS:
        val, quality = features.get(key, (None, "missing"))
        weight = BASELINE_WEIGHTS.get(key, 0)

        if quality != "ok" or val is None:
            continue

        ok_count += 1
        # Normalize: returns are already proportions; vol/sentiment scale differently
        if key.startswith("return_"):
            norm = max(-1, min(1, val / 0.15))  # 15% return = score 1
        elif key == "volatility_20d":
            norm = max(-1, min(1, val / 0.40))
        elif key == "drawdown_20d":
            norm = max(-1, min(1, val / 0.10))
        elif key == "relative_volume_20d":
            norm = max(-1, min(1, (val - 1.0) / 2.0))
        elif key == "news_sentiment_7d":
            norm = max(-1, min(1, val * 2))
        elif key == "news_count_7d":
            norm = max(-1, min(1, val / 10.0))
        else:
            norm = 0

        contribution = weight * norm
        score += contribution
        if abs(contribution) > 0.02:
            drivers.append(f"{key}: {val:.3f} → {contribution:+.3f}")

    score = max(-1, min(1, score))
    predicted_return = score * 0.10  # scale to ~±10% expected return
    confidence = min(0.85, 0.15 + (ok_count / max(total, 1)) * 0.60)

    quality = "ok" if ok_count >= 4 else "partial" if ok_count >= 2 else "insufficient_data"

    return {
        "prediction_value": round(predicted_return, 4),
        "prediction_score": round(score, 4),
        "confidence": round(confidence, 3),
        "quality": quality,
        "drivers": drivers,
        "ok_feature_count": ok_count,
        "total_feature_count": total,
    }


class ModelingService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def ensure_default_definitions(self) -> int:
        inserted = 0
        for defn in DEFAULT_MODELS:
            existing = (await self.db.execute(
                select(ModelDefinition.id).where(ModelDefinition.key == defn["key"])
            )).scalar()
            if not existing:
                self.db.add(ModelDefinition(id=gen_uuid(), **defn))
                inserted += 1
        if inserted:
            await self.db.commit()
        return inserted

    async def _get_latest_feature_set(self) -> FeatureSet | None:
        return (await self.db.execute(
            select(FeatureSet)
            .where(FeatureSet.status.in_(["completed", "partial"]))
            .order_by(FeatureSet.as_of.desc(), FeatureSet.created_at.desc())
            .limit(1)
        )).scalar_one_or_none()

    async def _get_feature_map(self, feature_set_id: str) -> dict[str, dict[str, tuple[float | None, str]]]:
        """Return {ticker: {feature_key: (value, quality)}} with asset_ids."""
        rows = (await self.db.execute(
            select(FeatureValue.ticker, FeatureValue.asset_id, FeatureValue.feature_key, FeatureValue.value, FeatureValue.quality)
            .where(FeatureValue.feature_set_id == feature_set_id)
        )).all()
        result: dict[str, dict] = {}
        asset_ids: dict[str, str] = {}
        for r in rows:
            if r.ticker not in result:
                result[r.ticker] = {}
                asset_ids[r.ticker] = r.asset_id
            result[r.ticker][r.feature_key] = (r.value, r.quality)
        return result, asset_ids

    async def train_baseline(self, model_key: str = "ml_return_forecaster",
                             train_start: date | None = None, train_end: date | None = None) -> ModelRun:
        """'Train' the baseline model — really just validates feature coverage and stores metadata.

        The baseline model has fixed weights, so training is a no-op for the model itself.
        This records the training context for lineage.
        """
        await self.ensure_default_definitions()
        now = datetime.now(timezone.utc)
        if train_end is None:
            train_end = date.today()
        if train_start is None:
            train_start = train_end - timedelta(days=60)

        fs = await self._get_latest_feature_set()
        warnings = []
        metrics = {"model_type": "baseline_linear", "weights": BASELINE_WEIGHTS}

        if not fs:
            warnings.append("No feature set available for training context")
            metrics["sample_count"] = 0
        else:
            fv_count = (await self.db.execute(
                select(func.count()).select_from(FeatureValue).where(FeatureValue.feature_set_id == fs.id)
            )).scalar() or 0
            metrics["sample_count"] = fv_count
            metrics["feature_set_id"] = fs.id
            metrics["feature_set_as_of"] = fs.as_of.isoformat() if fs.as_of else None
            if fv_count < 20:
                warnings.append(f"Limited training data: {fv_count} feature values")

        run = ModelRun(
            id=gen_uuid(), model_key=model_key, model_version="v1",
            run_type="train", status="completed",
            train_start_date=train_start, train_end_date=train_end,
            source_feature_set_ids=[fs.id] if fs else [],
            metrics=metrics, warnings=warnings if warnings else None,
            started_at=now, completed_at=datetime.now(timezone.utc),
        )
        self.db.add(run)
        await self.db.commit()
        return run

    async def predict(self, model_key: str = "ml_return_forecaster",
                      feature_set_id: str | None = None) -> ModelRun:
        """Generate predictions from the baseline model using feature_values."""
        await self.ensure_default_definitions()
        now = datetime.now(timezone.utc)

        if feature_set_id:
            fs = (await self.db.execute(
                select(FeatureSet).where(FeatureSet.id == feature_set_id)
            )).scalar_one_or_none()
        else:
            fs = await self._get_latest_feature_set()

        if not fs:
            run = ModelRun(
                id=gen_uuid(), model_key=model_key, model_version="v1",
                run_type="predict", status="failed",
                warnings=["No feature set available"],
                started_at=now, completed_at=now,
            )
            self.db.add(run)
            await self.db.commit()
            return run

        fv_map, asset_ids = await self._get_feature_map(fs.id)

        run = ModelRun(
            id=gen_uuid(), model_key=model_key, model_version="v1",
            run_type="predict", status="running",
            source_feature_set_ids=[fs.id],
            started_at=now,
        )
        self.db.add(run)

        pred_count = 0
        warnings = []
        for ticker, feats in fv_map.items():
            result = _baseline_predict(feats)
            aid = asset_ids.get(ticker, "")

            self.db.add(ModelPrediction(
                id=gen_uuid(), model_run_id=run.id,
                asset_id=aid, ticker=ticker,
                as_of=fs.as_of,
                prediction_horizon_days=20,
                prediction_value=result["prediction_value"],
                prediction_score=result["prediction_score"],
                confidence=result["confidence"],
                quality=result["quality"],
                drivers=result["drivers"],
            ))
            pred_count += 1

            if result["quality"] != "ok":
                warnings.append(f"{ticker}: {result['quality']} ({result['ok_feature_count']}/{result['total_feature_count']} features)")

        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        run.metrics = {
            "prediction_count": pred_count,
            "feature_set_id": fs.id,
            "as_of": fs.as_of.isoformat() if fs.as_of else None,
        }
        run.warnings = warnings if warnings else None

        await self.db.commit()
        return run

    async def get_definitions(self) -> list[ModelDefinition]:
        return list((await self.db.execute(
            select(ModelDefinition).order_by(ModelDefinition.key)
        )).scalars().all())

    async def get_runs(self, model_key: str | None = None, limit: int = 20) -> list[ModelRun]:
        stmt = select(ModelRun).order_by(ModelRun.created_at.desc()).limit(limit)
        if model_key:
            stmt = stmt.where(ModelRun.model_key == model_key)
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_predictions(self, model_key: str | None = None) -> list[ModelPrediction]:
        # Get latest predict run
        stmt = select(ModelRun).where(ModelRun.run_type == "predict").where(ModelRun.status == "completed")
        if model_key:
            stmt = stmt.where(ModelRun.model_key == model_key)
        stmt = stmt.order_by(ModelRun.completed_at.desc()).limit(1)
        run = (await self.db.execute(stmt)).scalar_one_or_none()
        if not run:
            return []
        return list((await self.db.execute(
            select(ModelPrediction).where(ModelPrediction.model_run_id == run.id)
        )).scalars().all())

    async def get_status(self) -> dict:
        total_defs = (await self.db.execute(select(func.count()).select_from(ModelDefinition))).scalar() or 0
        active = (await self.db.execute(
            select(func.count()).select_from(ModelDefinition)
            .where(ModelDefinition.status.in_(["active", "experimental"]))
        )).scalar() or 0
        total_runs = (await self.db.execute(select(func.count()).select_from(ModelRun))).scalar() or 0
        total_preds = (await self.db.execute(select(func.count()).select_from(ModelPrediction))).scalar() or 0
        latest = (await self.db.execute(
            select(ModelRun).order_by(ModelRun.created_at.desc()).limit(1)
        )).scalar_one_or_none()
        return {
            "total_definitions": total_defs,
            "active_definitions": active,
            "total_runs": total_runs,
            "total_predictions": total_preds,
            "latest_run_id": latest.id if latest else None,
            "latest_run_status": latest.status if latest else None,
        }
