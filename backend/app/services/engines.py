"""Engine runner service.

Phase 4C: reads persisted feature_values and writes signal_runs / signal_outputs.
Engines are deterministic analytical functions, not ML models.

Implemented engines:
  - technical_momentum: price momentum + volatility + drawdown
  - risk_quality: volatility + drawdown + volume profile
  - news_sentiment: news sentiment + news count
"""
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import gen_uuid
from app.models.engine import EngineDefinition
from app.models.feature import FeatureSet, FeatureValue
from app.models.signal import SignalOutput, SignalRun

# ── Default engine definitions ────────────────────────────────────────

DEFAULT_ENGINES = [
    {
        "key": "technical_momentum", "name": "Technical Momentum", "category": "momentum",
        "description": "Scores assets by price momentum, penalised by volatility and drawdown",
        "version": "v1", "output_kind": "signal",
        "required_feature_keys": ["return_5d", "return_20d", "return_60d", "volatility_20d", "drawdown_20d"],
    },
    {
        "key": "risk_quality", "name": "Risk & Quality", "category": "risk",
        "description": "Scores assets by risk metrics: volatility, drawdown, volume profile",
        "version": "v1", "output_kind": "signal",
        "required_feature_keys": ["volatility_20d", "drawdown_20d", "relative_volume_20d"],
    },
    {
        "key": "news_sentiment", "name": "News Sentiment", "category": "sentiment",
        "description": "Scores assets by aggregated news sentiment and coverage",
        "version": "v1", "output_kind": "signal",
        "required_feature_keys": ["news_sentiment_7d", "news_count_7d"],
    },
    {
        "key": "ml_return_forecaster", "name": "ML Return Forecaster (Baseline)", "category": "ml",
        "description": "Baseline ML engine — reads model_predictions from ml_return_forecaster model. "
                       "Experimental/shadow — does not dominate allocation. Clearly labeled baseline.",
        "version": "v1", "output_kind": "signal",
        "required_feature_keys": ["return_5d", "return_20d", "return_60d", "volatility_20d",
                                   "drawdown_20d", "relative_volume_20d", "news_sentiment_7d", "news_count_7d"],
    },
]


# ── Engine computation functions ──────────────────────────────────────

def _run_technical_momentum(features: dict[str, tuple[float | None, str]]) -> dict:
    """Technical momentum engine.

    Score formula:
      raw = 0.25 * return_5d_norm + 0.40 * return_20d_norm + 0.35 * return_60d_norm
      penalty = volatility_penalty + drawdown_penalty
      score = clamp(raw - penalty, -1, 1)

    Normalisation: return values are scaled by dividing by 0.20 (20% = score 1.0).
    Volatility penalty: vol_20d / 0.40 * 0.15 (high vol up to 15% penalty).
    Drawdown penalty: abs(dd_20d) / 0.10 * 0.10 (10% dd = 10% penalty).
    """
    r5, q5 = features.get("return_5d", (None, "missing"))
    r20, q20 = features.get("return_20d", (None, "missing"))
    r60, q60 = features.get("return_60d", (None, "missing"))
    vol, qv = features.get("volatility_20d", (None, "missing"))
    dd, qd = features.get("drawdown_20d", (None, "missing"))

    drivers = []
    caveats = []
    ok_count = sum(1 for q in [q5, q20, q60] if q == "ok")

    if ok_count == 0:
        return {"score": 0.0, "confidence": 0.1, "stance": "hold", "risk_level": "High",
                "drivers": [], "caveats": ["No momentum data available"]}

    def norm_ret(v):
        return max(-1, min(1, (v or 0) / 0.20))

    raw = 0.0
    if q5 == "ok" and r5 is not None:
        raw += 0.25 * norm_ret(r5)
        if r5 > 0.01:
            drivers.append(f"5d return +{r5:.1%}")
    if q20 == "ok" and r20 is not None:
        raw += 0.40 * norm_ret(r20)
        if r20 > 0.02:
            drivers.append(f"20d return +{r20:.1%}")
        elif r20 < -0.02:
            drivers.append(f"20d return {r20:.1%}")
    if q60 == "ok" and r60 is not None:
        raw += 0.35 * norm_ret(r60)
        if r60 > 0.05:
            drivers.append(f"60d return +{r60:.1%}")

    penalty = 0.0
    if qv == "ok" and vol is not None:
        penalty += min(vol / 0.40, 1.0) * 0.15
        if vol > 0.30:
            caveats.append(f"High volatility {vol:.1%}")
    if qd == "ok" and dd is not None:
        penalty += min(abs(dd) / 0.10, 1.0) * 0.10
        if abs(dd) > 0.05:
            caveats.append(f"Drawdown {dd:.1%}")

    score = max(-1, min(1, raw - penalty))
    confidence = min(0.95, 0.3 + ok_count * 0.15 + (0.1 if qv == "ok" else 0) + (0.1 if qd == "ok" else 0))

    if score >= 0.35:
        stance = "buy"
    elif score <= -0.25:
        stance = "sell"
    else:
        stance = "hold"

    risk_level = "Low" if (vol or 0) < 0.20 else "Moderate" if (vol or 0) < 0.35 else "Elevated" if (vol or 0) < 0.50 else "High"

    return {"score": round(score, 4), "confidence": round(confidence, 3), "stance": stance,
            "risk_level": risk_level, "drivers": drivers, "caveats": caveats}


def _run_risk_quality(features: dict[str, tuple[float | None, str]]) -> dict:
    """Risk & quality engine.

    Score formula:
      vol_score = 1.0 - clamp(vol / 0.50, 0, 1)   (lower vol = higher score)
      dd_score  = 1.0 - clamp(abs(dd) / 0.15, 0, 1) (shallower dd = higher)
      vol_score_adj = vol_score * relative_volume_factor
      score = 0.45 * vol_score + 0.35 * dd_score + 0.20 * vol_profile

    Stance: score < 0.30 => trim/sell, score > 0.60 => hold (favourable risk)
    """
    vol, qv = features.get("volatility_20d", (None, "missing"))
    dd, qd = features.get("drawdown_20d", (None, "missing"))
    rv, qr = features.get("relative_volume_20d", (None, "missing"))

    drivers = []
    caveats = []
    ok_count = sum(1 for q in [qv, qd, qr] if q == "ok")

    if ok_count == 0:
        return {"score": 0.0, "confidence": 0.15, "stance": "hold", "risk_level": "High",
                "drivers": [], "caveats": ["No risk data available"]}

    vol_score = 1.0 - min((vol or 0.25) / 0.50, 1.0) if qv == "ok" else 0.5
    dd_score = 1.0 - min(abs(dd or -0.05) / 0.15, 1.0) if qd == "ok" else 0.5
    vol_profile = min((rv or 1.0) / 2.0, 1.0) if qr == "ok" else 0.5

    if qv == "ok":
        drivers.append(f"Volatility {vol:.1%}" if vol else "Volatility n/a")
    if qd == "ok":
        drivers.append(f"Max drawdown {dd:.1%}" if dd else "Drawdown n/a")
    if qr == "ok" and rv is not None and rv < 0.5:
        caveats.append(f"Low relative volume {rv:.2f}x")

    score = 0.45 * vol_score + 0.35 * dd_score + 0.20 * vol_profile
    score = max(-1, min(1, score * 2 - 1))  # rescale 0-1 to -1..+1

    confidence = min(0.90, 0.25 + ok_count * 0.18)

    if score <= -0.30:
        stance = "trim"
    elif score <= -0.10:
        stance = "sell"
    elif score >= 0.30:
        stance = "hold"
    else:
        stance = "hold"

    risk_level = "Low" if score > 0.3 else "Moderate" if score > 0 else "Elevated" if score > -0.3 else "High"

    return {"score": round(score, 4), "confidence": round(confidence, 3), "stance": stance,
            "risk_level": risk_level, "drivers": drivers, "caveats": caveats}


def _run_news_sentiment(features: dict[str, tuple[float | None, str]]) -> dict:
    """News sentiment engine.

    Score formula:
      If news_count_7d == 0 and source exists: stance=hold, score=0, confidence=0.25, caveat
      If news_count_7d missing: degraded
      Otherwise: score = clamp(sentiment * 1.5, -1, 1), confidence from count coverage
    """
    sent, qs = features.get("news_sentiment_7d", (None, "missing"))
    count_val, qc = features.get("news_count_7d", (None, "missing"))
    count = int(count_val) if count_val is not None else 0

    drivers = []
    caveats = []

    if qc == "insufficient_data" and qs == "insufficient_data":
        return {"score": 0.0, "confidence": 0.10, "stance": "hold", "risk_level": "Moderate",
                "drivers": [], "caveats": ["News source unavailable for this window"]}

    if count == 0:
        return {"score": 0.0, "confidence": 0.25, "stance": "hold", "risk_level": "Moderate",
                "drivers": [], "caveats": ["No ticker-specific news in 7d window"]}

    score = max(-1, min(1, (sent or 0) * 1.5))
    confidence = min(0.85, 0.20 + count * 0.05)

    if sent is not None:
        label = "positive" if sent > 0.1 else "negative" if sent < -0.1 else "neutral"
        drivers.append(f"7d sentiment {sent:.3f} ({label}, {count} articles)")

    if score >= 0.30:
        stance = "buy"
    elif score <= -0.30:
        stance = "sell"
    else:
        stance = "hold"

    risk_level = "Low" if abs(score) < 0.3 else "Moderate"

    return {"score": round(score, 4), "confidence": round(confidence, 3), "stance": stance,
            "risk_level": risk_level, "drivers": drivers, "caveats": caveats}


# Engine dispatch table
ENGINE_FUNCTIONS = {
    "technical_momentum": _run_technical_momentum,
    "risk_quality": _run_risk_quality,
    "news_sentiment": _run_news_sentiment,
}


# ── Service class ────────────────────────────────────────────────────

class EngineService:
    """Runs engines against persisted feature_values and writes signal_runs/signal_outputs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def ensure_default_engines(self) -> int:
        inserted = 0
        for defn in DEFAULT_ENGINES:
            existing = (await self.db.execute(
                select(EngineDefinition.id).where(EngineDefinition.key == defn["key"])
            )).scalar()
            if not existing:
                self.db.add(EngineDefinition(id=gen_uuid(), **defn))
                inserted += 1
        if inserted:
            await self.db.commit()
        return inserted

    async def _get_active_engines(self, keys: list[str] | None = None) -> list[EngineDefinition]:
        stmt = select(EngineDefinition).where(EngineDefinition.is_active == True)  # noqa: E712
        if keys:
            stmt = stmt.where(EngineDefinition.key.in_(keys))
        return list((await self.db.execute(stmt)).scalars().all())

    async def _get_feature_values_map(self, feature_set_id: str) -> dict[str, dict[str, tuple[float | None, str]]]:
        """Return {ticker: {feature_key: (value, quality)}} from a feature set."""
        rows = (await self.db.execute(
            select(FeatureValue.ticker, FeatureValue.asset_id, FeatureValue.feature_key, FeatureValue.value, FeatureValue.quality)
            .where(FeatureValue.feature_set_id == feature_set_id)
        )).all()

        result: dict[str, dict[str, tuple[float | None, str]]] = {}
        asset_ids: dict[str, str] = {}
        for r in rows:
            if r.ticker not in result:
                result[r.ticker] = {}
                asset_ids[r.ticker] = r.asset_id
            result[r.ticker][r.feature_key] = (r.value, r.quality)

        return result, asset_ids

    async def _get_latest_feature_set(self) -> FeatureSet | None:
        return (await self.db.execute(
            select(FeatureSet)
            .where(FeatureSet.status.in_(["completed", "partial"]))
            .order_by(FeatureSet.as_of.desc(), FeatureSet.created_at.desc())
            .limit(1)
        )).scalar_one_or_none()

    async def run_engines(
        self,
        feature_set_id: str | None = None,
        engine_keys: list[str] | None = None,
    ) -> list[dict]:
        """Run active engines against a feature set. Returns list of run results."""
        now = datetime.now(UTC)
        await self.ensure_default_engines()

        # Resolve feature set
        if feature_set_id:
            fs = (await self.db.execute(
                select(FeatureSet).where(FeatureSet.id == feature_set_id)
            )).scalar_one_or_none()
        else:
            fs = await self._get_latest_feature_set()

        if not fs:
            return [{"run_id": "", "engine_key": "all", "status": "failed",
                     "signal_count": 0, "message": "No feature set available"}]

        engines = await self._get_active_engines(engine_keys)
        if not engines:
            return [{"run_id": "", "engine_key": "all", "status": "failed",
                     "signal_count": 0, "message": "No active engines"}]

        fv_map, asset_ids = await self._get_feature_values_map(fs.id)

        results = []
        for eng in engines:
            # ML engines read from model_predictions instead of feature_values
            if eng.category == "ml":
                signal_count = await self._run_ml_engine(eng, run, fs)
                run.status = "completed"
                run.run_completed_at = datetime.now(UTC)
                results.append({"run_id": run.id, "engine_key": eng.key, "status": "completed",
                                "signal_count": signal_count, "message": f"{signal_count} ML signals",
                                "feature_set_id": fs.id})
                continue

            engine_fn = ENGINE_FUNCTIONS.get(eng.key)
            if not engine_fn:
                results.append({"run_id": "", "engine_key": eng.key, "status": "skipped",
                                "signal_count": 0, "message": f"No implementation for {eng.key}"})
                continue

            run = SignalRun(
                id=gen_uuid(), engine_name=eng.key, engine_version=eng.version,
                feature_set_id=fs.id, run_started_at=now, status="running",
                data_as_of=datetime(fs.as_of.year, fs.as_of.month, fs.as_of.day, tzinfo=UTC),
            )
            self.db.add(run)

            signal_count = 0
            for ticker, feat_dict in fv_map.items():
                try:
                    output = engine_fn(feat_dict)
                    asset_id = asset_ids.get(ticker, "")

                    # Summarise feature quality for this asset
                    required = eng.required_feature_keys or []
                    ok_feats = sum(1 for k in required if feat_dict.get(k, (None, "missing"))[1] == "ok")
                    quality_summary = f"{ok_feats}/{len(required)} features ok" if required else "n/a"

                    self.db.add(SignalOutput(
                        id=gen_uuid(), signal_run_id=run.id, asset_id=asset_id,
                        score=output["score"], stance=output["stance"],
                        confidence=output["confidence"], rationale="; ".join(output["drivers"]) if output["drivers"] else None,
                        artifacts={
                            "risk_level": output["risk_level"],
                            "drivers": output["drivers"],
                            "caveats": output["caveats"],
                            "engine_key": eng.key,
                            "engine_name": eng.name,
                            "ticker": ticker,
                            "feature_quality": quality_summary,
                            "source_feature_set_id": fs.id,
                        },
                    ))
                    signal_count += 1
                except Exception as e:
                    # Partial failure: log but continue
                    self.db.add(SignalOutput(
                        id=gen_uuid(), signal_run_id=run.id, asset_id=asset_ids.get(ticker, ""),
                        score=0.0, stance="hold", confidence=0.0,
                        rationale=f"Engine error: {str(e)[:200]}",
                        artifacts={"error": str(e)[:200], "engine_key": eng.key, "ticker": ticker},
                    ))
                    signal_count += 1

            run.status = "completed"
            run.run_completed_at = datetime.now(UTC)

            results.append({"run_id": run.id, "engine_key": eng.key, "status": "completed",
                            "signal_count": signal_count, "message": f"{signal_count} signals",
                            "feature_set_id": fs.id})

        await self.db.commit()
        return results

    async def get_latest_run(self) -> SignalRun | None:
        return (await self.db.execute(
            select(SignalRun).order_by(SignalRun.run_completed_at.desc()).limit(1)
        )).scalar_one_or_none()

    async def _run_ml_engine(self, eng: EngineDefinition, run: SignalRun, fs: FeatureSet) -> int:
        """Run ML engine by reading latest model_predictions."""
        from app.models.modeling import ModelPrediction
        from app.models.modeling import ModelRun as MRun

        # Find latest completed predict run for this model key
        latest_run = (await self.db.execute(
            select(MRun)
            .where(MRun.model_key == eng.key)
            .where(MRun.run_type == "predict")
            .where(MRun.status == "completed")
            .order_by(MRun.completed_at.desc())
            .limit(1)
        )).scalar_one_or_none()

        if not latest_run:
            # No predictions available — produce hold signals with low confidence
            self.db.add(SignalOutput(
                id=gen_uuid(), signal_run_id=run.id, asset_id="",
                score=0.0, stance="hold", confidence=0.05,
                rationale="No ML predictions available — model not yet trained/predicted",
                artifacts={"engine_key": eng.key, "engine_name": eng.name,
                           "caveats": ["No model predictions available"], "drivers": [],
                           "risk_level": "Moderate", "ticker": "ALL",
                           "source_feature_set_id": fs.id if fs else None},
            ))
            return 1

        preds = (await self.db.execute(
            select(ModelPrediction).where(ModelPrediction.model_run_id == latest_run.id)
        )).scalars().all()

        count = 0
        for p in preds:
            score = p.prediction_score or 0
            conf = p.confidence or 0.2
            if score >= 0.25:
                stance = "buy"
            elif score <= -0.25:
                stance = "sell"
            else:
                stance = "hold"

            risk = "Low" if abs(score) < 0.2 else "Moderate" if abs(score) < 0.5 else "Elevated"
            drivers = p.drivers or []
            caveats = ["ML baseline / experimental / shadow"]
            if p.quality != "ok":
                caveats.append(f"Prediction quality: {p.quality}")

            self.db.add(SignalOutput(
                id=gen_uuid(), signal_run_id=run.id, asset_id=p.asset_id,
                score=score, stance=stance, confidence=conf,
                rationale="; ".join(drivers[:3]) if drivers else "ML baseline prediction",
                artifacts={
                    "engine_key": eng.key, "engine_name": eng.name,
                    "ticker": p.ticker, "risk_level": risk,
                    "drivers": drivers, "caveats": caveats,
                    "source_feature_set_id": fs.id if fs else None,
                    "source_model_run_id": latest_run.id,
                },
            ))
            count += 1

        return count

    async def _get_registered_keys(self) -> set[str]:
        """Return the set of active engine definition keys."""
        rows = (await self.db.execute(
            select(EngineDefinition.key).where(EngineDefinition.is_active == True)  # noqa: E712
        )).scalars().all()
        return set(rows)

    async def get_latest_signals(self, registered_only: bool = True) -> list[SignalOutput]:
        """Get signal outputs from the latest completed run of each active registered engine.

        When registered_only=True (default), only runs whose engine_name matches
        an active EngineDefinition.key are included. This excludes legacy seeded
        runs (momentum, fundamentals, narrative, riskparity, flow) that predate
        the Phase 4C engine registry.
        """
        await self.ensure_default_engines()
        registered = await self._get_registered_keys() if registered_only else None

        runs = (await self.db.execute(
            select(SignalRun.id, SignalRun.engine_name)
            .where(SignalRun.status == "completed")
            .order_by(SignalRun.run_completed_at.desc())
        )).all()

        seen_engines = set()
        run_ids = []
        for r in runs:
            if r.engine_name in seen_engines:
                continue
            if registered is not None and r.engine_name not in registered:
                continue
            seen_engines.add(r.engine_name)
            run_ids.append(r.id)

        if not run_ids:
            return []

        return list((await self.db.execute(
            select(SignalOutput).where(SignalOutput.signal_run_id.in_(run_ids))
        )).scalars().all())

    async def get_runs(self, limit: int = 50) -> list[dict]:
        """Return recent signal runs with output counts."""
        runs = (await self.db.execute(
            select(SignalRun).order_by(SignalRun.run_completed_at.desc()).limit(limit)
        )).scalars().all()

        result = []
        for r in runs:
            count = (await self.db.execute(
                select(func.count()).select_from(SignalOutput).where(SignalOutput.signal_run_id == r.id)
            )).scalar() or 0
            result.append({
                "run_id": r.id,
                "engine_name": r.engine_name,
                "engine_version": r.engine_version,
                "feature_set_id": r.feature_set_id,
                "status": r.status,
                "run_started_at": r.run_started_at,
                "run_completed_at": r.run_completed_at,
                "data_as_of": r.data_as_of,
                "signal_count": count,
            })
        return result

    async def get_run(self, run_id: str) -> dict | None:
        """Return a single signal run with output count."""
        r = (await self.db.execute(
            select(SignalRun).where(SignalRun.id == run_id)
        )).scalar_one_or_none()
        if not r:
            return None
        count = (await self.db.execute(
            select(func.count()).select_from(SignalOutput).where(SignalOutput.signal_run_id == r.id)
        )).scalar() or 0
        return {
            "run_id": r.id,
            "engine_name": r.engine_name,
            "engine_version": r.engine_version,
            "feature_set_id": r.feature_set_id,
            "status": r.status,
            "run_started_at": r.run_started_at,
            "run_completed_at": r.run_completed_at,
            "data_as_of": r.data_as_of,
            "signal_count": count,
        }

    async def get_status(self) -> dict:
        total = (await self.db.execute(select(func.count()).select_from(EngineDefinition))).scalar() or 0
        active = (await self.db.execute(
            select(func.count()).select_from(EngineDefinition).where(EngineDefinition.is_active == True)  # noqa: E712
        )).scalar() or 0
        latest = await self.get_latest_run()
        return {
            "total_definitions": total,
            "active_definitions": active,
            "latest_run_id": latest.id if latest else None,
            "latest_run_at": latest.run_completed_at if latest else None,
            "latest_run_status": latest.status if latest else None,
            "latest_feature_set_id": latest.feature_set_id if latest else None,
        }
