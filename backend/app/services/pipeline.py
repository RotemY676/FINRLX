"""Decision pipeline service.

Phase 4D: Selection → Allocation → Timing → Risk Overlay → Recommendation.
Reads persisted signal_outputs and writes pipeline stage records + recommendation.

Doc 10 Section 8 steps 5-9:
  5. Execute selection policy
  6. Execute allocation policy
  7. Execute timing policy
  8. Execute risk overlay
  9. Publish (deferred to Phase 4E — recommendation created as 'draft')
"""
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import gen_uuid
from app.models.decision_pipeline import AllocationResult, RiskOverlayResult, SelectionRun, TimingResult
from app.models.feature import FeatureSet
from app.models.ops import AuditEvent
from app.models.recommendation import Recommendation, RecommendationWeight
from app.models.reference import Asset, Universe, UniverseMembership
from app.models.signal import SignalOutput, SignalRun
from app.services.engines import EngineService
from app.services.profile_pipeline_overrides import (
    ProfileOverrides,
    cap_confidence,
    cap_position_weight,
    filter_universe_by_profile,
)
from app.services.provenance import (
    PIPELINE_VERSION,
    compute_input_hash,
    compute_policy_hash,
    new_replay_seed,
)

# ── Policy constants ──────────────────────────────────────────────────

MAX_POSITION_WEIGHT = 0.15  # 15% cap per asset
MIN_POSITION_WEIGHT = 0.02  # 2% floor for selected assets
MAX_INVESTED = 0.95         # 95% max invested
CASH_RESERVE = 0.05         # 5% cash floor
SELECTION_THRESHOLD = -0.50 # include assets with aggregate score above this (generous)
CONFIDENCE_FLOOR = 0.20     # trim assets below this confidence
HIGH_RISK_TRIM = 0.70       # reduce weight by 30% for high-risk assets


def _policy_snapshot() -> dict[str, float]:
    """Snapshot the policy constants that affect recommendation outputs."""
    return {
        "MAX_POSITION_WEIGHT": MAX_POSITION_WEIGHT,
        "MIN_POSITION_WEIGHT": MIN_POSITION_WEIGHT,
        "MAX_INVESTED": MAX_INVESTED,
        "CASH_RESERVE": CASH_RESERVE,
        "SELECTION_THRESHOLD": SELECTION_THRESHOLD,
        "CONFIDENCE_FLOOR": CONFIDENCE_FLOOR,
        "HIGH_RISK_TRIM": HIGH_RISK_TRIM,
    }


class DecisionPipelineService:
    """Orchestrates the full decision pipeline from signals to recommendation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_universe(
        self,
        universe_id: str | None,
        profile_overrides: ProfileOverrides | None = None,
    ) -> tuple[str, list[tuple[str, str]]]:
        """Return (universe_id, [(asset_id, ticker)]) — use first universe if none specified.

        Phase W-5: when ``profile_overrides`` is set with non-empty sector
        lists, the resulting asset list is filtered to honor them.
        """
        if not universe_id:
            # Phase 20.1 — default-universe lookup must be deterministic AND
            # filter out deactivated universes. Without ORDER BY, SQLite
            # returns rows in implementation-defined order, so once Phase 20
            # introduced the ability to create multiple universes, the
            # pipeline started occasionally picking an empty or inactive one
            # and silently failing the run.
            uni = (await self.db.execute(
                select(Universe.id)
                .where(Universe.is_active.is_(True))
                .order_by(Universe.created_at.asc())
                .limit(1)
            )).scalar()
            universe_id = uni
        if not universe_id:
            return None, []
        rows = (await self.db.execute(
            select(Asset.id, Asset.ticker)
            .join(UniverseMembership, UniverseMembership.asset_id == Asset.id)
            .where(UniverseMembership.universe_id == universe_id)
        )).all()
        universe_assets = [(r.id, r.ticker) for r in rows]
        if profile_overrides is not None:
            universe_assets = await filter_universe_by_profile(
                self.db, universe_assets, profile_overrides
            )
        return universe_id, universe_assets

    async def _get_live_engine_keys(self) -> set[str]:
        """Return engine keys that are non-shadow (category != 'ml' or explicitly active non-experimental)."""
        from app.models.engine import EngineDefinition
        rows = (await self.db.execute(
            select(EngineDefinition.key)
            .where(EngineDefinition.is_active == True)  # noqa: E712
            .where(EngineDefinition.category != "ml")
        )).scalars().all()
        return set(rows)

    async def _get_registered_signals(self, signal_run_ids: list[str] | None = None, feature_set_id: str | None = None, include_shadow: bool = False) -> tuple[list[SignalOutput], list[str], str | None]:
        """Get signals from engine runs. Returns (outputs, run_ids, feature_set_id).

        By default excludes shadow/ML engines. Set include_shadow=True to include them.
        """
        eng_svc = EngineService(self.db)
        if include_shadow:
            registered_keys = await eng_svc._get_registered_keys()
        else:
            registered_keys = await self._get_live_engine_keys()

        # If explicit signal_run_ids provided, validate and use them
        if signal_run_ids:
            runs = (await self.db.execute(
                select(SignalRun)
                .where(SignalRun.id.in_(signal_run_ids))
                .where(SignalRun.status == "completed")
            )).scalars().all()

            # Filter to registered engines only
            valid_runs = [r for r in runs if r.engine_name in registered_keys]
            if not valid_runs:
                return [], [], None

            # Verify consistent feature_set_id
            fs_ids = {r.feature_set_id for r in valid_runs if r.feature_set_id}
            common_fs = fs_ids.pop() if len(fs_ids) == 1 else (fs_ids.pop() if fs_ids else None)

            run_ids = [r.id for r in valid_runs]
            outputs = list((await self.db.execute(
                select(SignalOutput).where(SignalOutput.signal_run_id.in_(run_ids))
            )).scalars().all())
            return outputs, run_ids, common_fs

        # If specific feature_set_id is provided, use it directly
        if feature_set_id:
            runs = (await self.db.execute(
                select(SignalRun)
                .where(SignalRun.feature_set_id == feature_set_id)
                .where(SignalRun.status == "completed")
                .where(SignalRun.engine_name.in_(registered_keys))
            )).scalars().all()
            if runs:
                run_ids = [r.id for r in runs]
                outputs = list((await self.db.execute(
                    select(SignalOutput).where(SignalOutput.signal_run_id.in_(run_ids))
                )).scalars().all())
                if outputs:
                    return outputs, run_ids, feature_set_id

        # Find a feature set that has registered engine runs linked to it.
        # Prefer the most recent as_of, but require actual signal coverage.
        fs_candidates = (await self.db.execute(
            select(FeatureSet)
            .where(FeatureSet.status.in_(["completed", "partial"]))
            .order_by(FeatureSet.as_of.desc(), FeatureSet.created_at.desc())
            .limit(20)
        )).scalars().all()

        for fs in fs_candidates:
            runs = (await self.db.execute(
                select(SignalRun)
                .where(SignalRun.feature_set_id == fs.id)
                .where(SignalRun.status == "completed")
                .where(SignalRun.engine_name.in_(registered_keys))
            )).scalars().all()
            if runs:
                run_ids = [r.id for r in runs]
                outputs = list((await self.db.execute(
                    select(SignalOutput).where(SignalOutput.signal_run_id.in_(run_ids))
                )).scalars().all())
                if outputs:
                    return outputs, run_ids, fs.id

        # No feature set has engine runs — return empty
        return [], [], None

    def _aggregate_asset_signals(self, outputs: list[SignalOutput]) -> dict[str, dict]:
        """Group signals by asset_id and compute aggregate score/stance/confidence."""
        by_asset: dict[str, list[SignalOutput]] = {}
        for o in outputs:
            by_asset.setdefault(o.asset_id, []).append(o)

        result = {}
        for asset_id, signals in by_asset.items():
            # Stance scoring: buy=+1, hold=0, trim=-0.5, sell=-1
            stance_map = {"buy": 1.0, "hold": 0.0, "trim": -0.5, "sell": -1.0}
            weighted_score = 0.0
            total_conf = 0.0
            drivers = []
            caveats = []
            ticker = "?"

            for s in signals:
                arts = s.artifacts or {}
                ticker = arts.get("ticker", ticker)
                conf = s.confidence or 0.0
                raw_score = s.score or 0.0
                stance_val = stance_map.get(s.stance or "hold", 0.0)

                # Combine raw score with stance direction, weighted by confidence
                combined = (raw_score * 0.6 + stance_val * 0.4) * max(conf, 0.1)
                weighted_score += combined
                total_conf += conf
                drivers.extend(arts.get("drivers", []))
                caveats.extend(arts.get("caveats", []))

            n = len(signals)
            avg_score = weighted_score / n if n > 0 else 0.0
            avg_conf = total_conf / n if n > 0 else 0.0

            # Determine aggregate stance
            if avg_score >= 0.15:
                agg_stance = "overweight"
            elif avg_score >= 0.0:
                agg_stance = "neutral"
            elif avg_score >= -0.15:
                agg_stance = "underweight"
            else:
                agg_stance = "exit"

            # Risk level from caveats
            risk_level = "High" if len(caveats) > 2 else "Elevated" if caveats else "Moderate"

            result[asset_id] = {
                "ticker": ticker,
                "score": round(avg_score, 4),
                "confidence": round(avg_conf, 3),
                "stance": agg_stance,
                "n_engines": n,
                "risk_level": risk_level,
                "drivers": list(dict.fromkeys(drivers))[:5],
                "caveats": list(dict.fromkeys(caveats))[:3],
            }

        return result

    # ── Stage: Selection ──────────────────────────────────────────────

    async def run_selection(
        self, rec_id: str, universe_id: str, asset_signals: dict[str, dict],
        universe_assets: list[tuple[str, str]],
    ) -> SelectionRun:
        """Select candidate assets above threshold from engine signals."""
        included = []
        excluded = []
        {aid for aid, _ in universe_assets}

        for asset_id, ticker in universe_assets:
            sig = asset_signals.get(asset_id)
            if not sig:
                excluded.append({"asset_id": asset_id, "ticker": ticker, "reason": "No engine signal coverage"})
                continue
            if sig["score"] >= SELECTION_THRESHOLD:
                included.append({
                    "asset_id": asset_id, "ticker": ticker,
                    "reason": f"Score {sig['score']:.3f} ({sig['stance']}, {sig['n_engines']} engines, conf {sig['confidence']:.2f})",
                })
            else:
                excluded.append({
                    "asset_id": asset_id, "ticker": ticker,
                    "reason": f"Score {sig['score']:.3f} below threshold {SELECTION_THRESHOLD}",
                })

        sel = SelectionRun(
            id=gen_uuid(), recommendation_id=rec_id, universe_id=universe_id,
            included_assets=included, excluded_assets=excluded,
            rationale=f"Selected {len(included)} of {len(universe_assets)} assets (threshold {SELECTION_THRESHOLD})",
        )
        self.db.add(sel)
        return sel

    # ── Stage: Allocation ─────────────────────────────────────────────

    async def run_allocation(
        self, rec_id: str, sel: SelectionRun, asset_signals: dict[str, dict],
    ) -> AllocationResult:
        """Convert selected assets into normalized target weights."""
        included = sel.included_assets or []
        if not included:
            alloc = AllocationResult(
                id=gen_uuid(), recommendation_id=rec_id, selection_run_id=sel.id,
                weights={}, method="score-weighted", rationale="No assets selected",
            )
            self.db.add(alloc)
            return alloc

        # Compute raw weights from positive scores
        raw = {}
        for entry in included:
            aid = entry["asset_id"]
            sig = asset_signals.get(aid, {})
            score = max(sig.get("score", 0), 0.001)  # floor at tiny positive
            raw[aid] = score

        total_raw = sum(raw.values())
        if total_raw <= 0:
            total_raw = 1.0

        # Normalize to MAX_INVESTED, enforce caps
        weights = {}
        for aid, score in raw.items():
            w = (score / total_raw) * MAX_INVESTED
            w = min(w, MAX_POSITION_WEIGHT)
            w = max(w, MIN_POSITION_WEIGHT)
            weights[aid] = round(w, 4)

        # Re-normalize if sum exceeds MAX_INVESTED
        total = sum(weights.values())
        if total > MAX_INVESTED:
            scale = MAX_INVESTED / total
            weights = {aid: round(w * scale, 4) for aid, w in weights.items()}

        alloc = AllocationResult(
            id=gen_uuid(), recommendation_id=rec_id, selection_run_id=sel.id,
            weights=weights, method="score-weighted",
            rationale=f"Allocated {len(weights)} positions, total invested {sum(weights.values()):.1%}, cash {1-sum(weights.values()):.1%}",
        )
        self.db.add(alloc)
        return alloc

    # ── Stage: Timing ─────────────────────────────────────────────────

    async def run_timing(
        self, rec_id: str, alloc: AllocationResult, asset_signals: dict[str, dict],
    ) -> TimingResult:
        """Classify timing urgency per asset based on signal confidence and risk."""
        weights = alloc.weights or {}
        entry_signals = {}
        exit_signals = {}
        urgency_votes = []

        for aid, _w in weights.items():
            sig = asset_signals.get(aid, {})
            conf = sig.get("confidence", 0.5)
            risk = sig.get("risk_level", "Moderate")
            stance = sig.get("stance", "neutral")

            if conf >= 0.6 and risk in ("Low", "Moderate") and stance == "overweight":
                entry_signals[aid] = "enter_now"
                urgency_votes.append("soon")
            elif conf >= 0.4:
                entry_signals[aid] = "stage_in"
                urgency_votes.append("soon")
            else:
                entry_signals[aid] = "defer"
                urgency_votes.append("wait")

            if stance == "exit":
                exit_signals[aid] = "reduce"

        # Overall urgency
        if urgency_votes.count("soon") > len(urgency_votes) / 2:
            urgency = "soon"
        else:
            urgency = "wait"

        timing = TimingResult(
            id=gen_uuid(), recommendation_id=rec_id,
            urgency=urgency, horizon_days=90,
            entry_signals=entry_signals, exit_signals=exit_signals,
            rationale=f"Timing: {urgency}, {len(entry_signals)} entries, {len(exit_signals)} exits",
        )
        self.db.add(timing)
        return timing

    # ── Stage: Risk Overlay ───────────────────────────────────────────

    async def run_risk_overlay(
        self,
        rec_id: str,
        alloc: AllocationResult,
        asset_signals: dict[str, dict],
        profile_overrides: ProfileOverrides | None = None,
    ) -> RiskOverlayResult:
        """Enforce portfolio-level risk controls on allocation weights.

        Phase W-5: when ``profile_overrides`` is set, the per-asset cap
        is tightened to ``min(MAX_POSITION_WEIGHT, profile.max_position_pct)``.
        """
        pre_weights = dict(alloc.weights or {})
        post_weights = dict(pre_weights)
        adjustments = []
        effective_cap = cap_position_weight(MAX_POSITION_WEIGHT, profile_overrides)
        constraints = [
            f"max_position_{int(round(effective_cap * 100))}pct",
            "confidence_floor_20pct",
            "high_risk_trim_30pct",
            "cash_reserve_5pct",
        ]
        if profile_overrides is not None:
            constraints.append(f"profile_bucket_{profile_overrides.risk_bucket}")

        for aid, w in list(post_weights.items()):
            sig = asset_signals.get(aid, {})
            ticker = sig.get("ticker", "?")
            conf = sig.get("confidence", 0.5)
            risk = sig.get("risk_level", "Moderate")

            # Max position cap (profile-aware)
            if w > effective_cap:
                new_w = effective_cap
                adjustments.append({"asset_id": aid, "ticker": ticker,
                    "reason": f"Capped at {effective_cap:.0%}", "delta": round(new_w - w, 4)})
                post_weights[aid] = new_w

            # Confidence floor
            if conf < CONFIDENCE_FLOOR:
                new_w = post_weights[aid] * 0.5
                adjustments.append({"asset_id": aid, "ticker": ticker,
                    "reason": f"Low confidence {conf:.2f} < {CONFIDENCE_FLOOR}", "delta": round(new_w - post_weights[aid], 4)})
                post_weights[aid] = round(new_w, 4)

            # High-risk trim
            if risk in ("High", "Elevated"):
                trim_factor = HIGH_RISK_TRIM
                new_w = post_weights[aid] * trim_factor
                adjustments.append({"asset_id": aid, "ticker": ticker,
                    "reason": f"Risk={risk}, trimmed to {trim_factor:.0%}", "delta": round(new_w - post_weights[aid], 4)})
                post_weights[aid] = round(new_w, 4)

        # Ensure total <= MAX_INVESTED
        total = sum(post_weights.values())
        if total > MAX_INVESTED:
            scale = MAX_INVESTED / total
            post_weights = {aid: round(w * scale, 4) for aid, w in post_weights.items()}

        # Portfolio risk score: avg of individual risk levels
        risk_scores = {"Low": 0.2, "Moderate": 0.4, "Elevated": 0.6, "High": 0.8}
        risk_vals = [risk_scores.get(asset_signals.get(aid, {}).get("risk_level", "Moderate"), 0.4)
                     for aid in post_weights]
        portfolio_risk = round(sum(risk_vals) / max(len(risk_vals), 1), 3)

        overlay = RiskOverlayResult(
            id=gen_uuid(), recommendation_id=rec_id,
            pre_risk_weights=pre_weights, post_risk_weights=post_weights,
            adjustments=adjustments, constraints_applied=constraints,
            portfolio_risk_score=portfolio_risk,
            rationale=f"Risk overlay: {len(adjustments)} adjustments, portfolio risk {portfolio_risk:.2f}",
        )
        self.db.add(overlay)
        return overlay

    # ── Generate Recommendation ───────────────────────────────────────

    async def generate_recommendation(
        self, rec_id: str, universe_id: str,
        overlay: RiskOverlayResult, asset_signals: dict[str, dict],
        feature_set_id: str | None, signal_run_ids: list[str] | None,
        warnings: list[str],
        signal_outputs: list[SignalOutput] | None = None,
        profile_overrides: ProfileOverrides | None = None,
    ) -> Recommendation:
        """Create the final recommendation with weights and confidence triplet.

        Phase W-5: when ``profile_overrides`` is set, the final
        ``model_confidence`` is clipped to the profile's confidence_cap
        and the rationale notes the profile binding.
        """
        now = datetime.now(UTC)
        final_weights = overlay.post_risk_weights or {}

        # Confidence triplet (profile-aware: cap to user's risk-bucket ceiling)
        confidences = [asset_signals.get(aid, {}).get("confidence", 0.5) for aid in final_weights]
        raw_model_conf = round(sum(confidences) / max(len(confidences), 1), 3)
        model_conf = round(cap_confidence(raw_model_conf, profile_overrides), 3)
        data_conf = 0.90  # will be refined when feature freshness is checked
        operational_conf = 0.95 if not warnings else max(0.5, 0.95 - len(warnings) * 0.05)

        # Rationale
        n_positions = len([w for w in final_weights.values() if w > 0.005])
        total_invested = sum(final_weights.values())
        rationale = (
            f"Pipeline-generated recommendation with {n_positions} positions, "
            f"total invested {total_invested:.1%}. "
            f"Based on {len(signal_run_ids or [])} engine runs."
        )
        if warnings:
            rationale += f" Warnings: {'; '.join(warnings[:3])}"

        # Get existing recommendation to compute deltas
        prev = (await self.db.execute(
            select(Recommendation).order_by(Recommendation.created_at.desc()).limit(1)
        )).scalar_one_or_none()

        prev_weights_map = {}
        if prev and prev.id != rec_id:
            prev_wt_rows = (await self.db.execute(
                select(RecommendationWeight).where(RecommendationWeight.recommendation_id == prev.id)
            )).scalars().all()
            prev_weights_map = {w.asset_id: w.target_weight for w in prev_wt_rows}

        rec = (await self.db.execute(
            select(Recommendation).where(Recommendation.id == rec_id)
        )).scalar_one_or_none()
        if rec:
            rec.status = "draft"
            rec.model_confidence = model_conf
            rec.data_confidence = data_conf
            rec.operational_confidence = operational_conf
            rec.valid_from = now
            rec.valid_to = now + timedelta(days=90)
            rec.rationale_summary = rationale
            rec.warnings = warnings if warnings else []
            rec.data_as_of = now
            rec.source_feature_set_id = feature_set_id
            rec.source_signal_run_ids = signal_run_ids
            # Provenance (Phase MVP-3): bind the recommendation to its exact inputs.
            # input_hash is computed in run_pipeline eagerly (before stages mutate state)
            # and only filled here if a caller passed signal_outputs directly.
            if signal_outputs is not None and rec.input_hash is None:
                rec.input_hash = compute_input_hash(signal_outputs)
            rec.policy_hash = compute_policy_hash(_policy_snapshot())

        # Create weight rows
        for aid, w in final_weights.items():
            if w < 0.001:
                continue
            sig = asset_signals.get(aid, {})
            prev_w = prev_weights_map.get(aid, 0.0)
            delta = round(w - prev_w, 4)
            stance = sig.get("stance", "neutral")

            self.db.add(RecommendationWeight(
                id=gen_uuid(), recommendation_id=rec_id, asset_id=aid,
                target_weight=w, previous_weight=prev_w, delta=delta,
                stance=stance,
                rationale="; ".join(sig.get("drivers", [])[:2]) if sig.get("drivers") else None,
            ))

        return rec

    # ── Full Pipeline ─────────────────────────────────────────────────

    async def run_pipeline(
        self,
        signal_run_ids: list[str] | None = None,
        universe_id: str | None = None,
        feature_set_id: str | None = None,
        include_shadow_engines: bool = False,
        profile_overrides: ProfileOverrides | None = None,
    ) -> dict:
        """Run the complete decision pipeline: Selection → Allocation → Timing → Risk → Recommendation.

        Phase W-5: when ``profile_overrides`` is set, the universe is
        filtered by the user's sector lists and the risk overlay uses
        the profile's per-asset cap. Behavior with overrides=None is
        unchanged from earlier phases (regression-covered by tests).
        """
        warnings = []
        stages = []

        if include_shadow_engines:
            warnings.append("Shadow/experimental ML signals included in this pipeline run.")
        if profile_overrides is not None:
            warnings.append(
                f"Profile-aware pipeline run: bucket={profile_overrides.risk_bucket}, "
                f"horizon={profile_overrides.horizon_band}"
            )

        # 1. Get signals (exclude shadow by default)
        outputs, run_ids, fs_id = await self._get_registered_signals(signal_run_ids, feature_set_id, include_shadow=include_shadow_engines)
        if not outputs:
            return {
                "recommendation_id": None, "status": "failed",
                "stages": [{"stage": "signals", "status": "failed", "record_id": None, "message": "No registered engine signals available"}],
                "warnings": ["No engine signals. Run /api/v1/engines/run first."],
                "feature_set_id": None, "signal_run_ids": [],
                "message": "Pipeline failed: no engine signals available",
            }

        # 2. Get universe (profile-filtered when overrides set)
        universe_id, universe_assets = await self._get_universe(universe_id, profile_overrides)
        if not universe_assets:
            return {
                "recommendation_id": None, "status": "failed",
                "stages": [{"stage": "universe", "status": "failed", "record_id": None, "message": "No assets in universe"}],
                "warnings": ["No universe/assets found."],
                "feature_set_id": fs_id, "signal_run_ids": run_ids,
                "message": "Pipeline failed: no assets in universe",
            }

        # 3. Aggregate signals
        asset_signals = self._aggregate_asset_signals(outputs)

        # Create recommendation record first (stages reference it).
        # Provenance is set eagerly here — before any stage runs — so the input
        # hash binds to the immutable signal set we're about to process, not
        # whatever the ORM identity-map shows at write time.
        rec_id = gen_uuid()
        now = datetime.now(UTC)
        rec = Recommendation(
            id=rec_id, universe_id=universe_id, status="draft",
            source_feature_set_id=fs_id, source_signal_run_ids=run_ids,
            pipeline_version=PIPELINE_VERSION,
            replay_seed=new_replay_seed(),
            input_hash=compute_input_hash(outputs),
        )
        self.db.add(rec)

        # 4. Selection
        sel = await self.run_selection(rec_id, universe_id, asset_signals, universe_assets)
        n_selected = len(sel.included_assets or [])
        stages.append({"stage": "selection", "status": "completed", "record_id": sel.id,
                       "message": f"Selected {n_selected} assets"})
        if n_selected == 0:
            warnings.append("No assets passed selection threshold")

        # 5. Allocation
        alloc = await self.run_allocation(rec_id, sel, asset_signals)
        stages.append({"stage": "allocation", "status": "completed", "record_id": alloc.id,
                       "message": f"Allocated {len(alloc.weights or {})} positions"})

        # 6. Timing
        timing = await self.run_timing(rec_id, alloc, asset_signals)
        stages.append({"stage": "timing", "status": "completed", "record_id": timing.id,
                       "message": f"Urgency: {timing.urgency}"})

        # 7. Risk overlay (profile-aware when overrides set)
        overlay = await self.run_risk_overlay(rec_id, alloc, asset_signals, profile_overrides)
        stages.append({"stage": "risk_overlay", "status": "completed", "record_id": overlay.id,
                       "message": f"{len(overlay.adjustments or [])} adjustments"})

        # 8. Generate recommendation (profile-aware confidence cap when set)
        rec = await self.generate_recommendation(
            rec_id, universe_id, overlay, asset_signals, fs_id, run_ids, warnings,
            signal_outputs=outputs, profile_overrides=profile_overrides,
        )
        stages.append({"stage": "recommendation", "status": "completed", "record_id": rec_id,
                       "message": "Draft recommendation created"})

        # Audit event
        self.db.add(AuditEvent(
            actor="pipeline", action="generate_recommendation",
            object_type="recommendation", object_id=rec_id,
            details={"stages": len(stages), "feature_set_id": fs_id, "signal_run_ids": run_ids},
            occurred_at=now,
        ))

        await self.db.commit()

        return {
            "recommendation_id": rec_id, "status": "completed",
            "stages": stages, "warnings": warnings,
            "feature_set_id": fs_id, "signal_run_ids": run_ids,
            "message": f"Pipeline completed: draft recommendation {rec_id[:8]}… with {len(alloc.weights or {})} positions",
        }

    async def get_latest_pipeline_recommendation(self) -> Recommendation | None:
        """Get latest pipeline-generated recommendation (has source lineage)."""
        return (await self.db.execute(
            select(Recommendation)
            .where(Recommendation.source_feature_set_id.is_not(None))
            .order_by(Recommendation.created_at.desc())
            .limit(1)
        )).scalar_one_or_none()

    async def get_pipeline_runs(self, limit: int = 50) -> list[dict]:
        """List pipeline-generated recommendations as pipeline runs."""
        recs = (await self.db.execute(
            select(Recommendation)
            .where(Recommendation.source_feature_set_id.is_not(None))
            .order_by(Recommendation.created_at.desc())
            .limit(limit)
        )).scalars().all()

        result = []
        for r in recs:
            wt_count = (await self.db.execute(
                select(func.count()).select_from(RecommendationWeight)
                .where(RecommendationWeight.recommendation_id == r.id)
            )).scalar() or 0
            warning_list = r.warnings if isinstance(r.warnings, list) else []
            result.append({
                "recommendation_id": r.id,
                "status": r.status,
                "created_at": r.created_at,
                "source_feature_set_id": r.source_feature_set_id,
                "source_signal_run_ids": r.source_signal_run_ids,
                "weight_count": wt_count,
                "model_confidence": r.model_confidence,
                "data_confidence": r.data_confidence,
                "operational_confidence": r.operational_confidence,
                "warning_count": len(warning_list),
            })
        return result

    async def get_pipeline_run_detail(self, recommendation_id: str) -> dict | None:
        """Get full pipeline run detail including all stage records."""
        rec = (await self.db.execute(
            select(Recommendation).where(Recommendation.id == recommendation_id)
            .where(Recommendation.source_feature_set_id.is_not(None))
        )).scalar_one_or_none()
        if not rec:
            return None

        sel = (await self.db.execute(
            select(SelectionRun).where(SelectionRun.recommendation_id == rec.id)
        )).scalar_one_or_none()
        alloc = (await self.db.execute(
            select(AllocationResult).where(AllocationResult.recommendation_id == rec.id)
        )).scalar_one_or_none()
        timing = (await self.db.execute(
            select(TimingResult).where(TimingResult.recommendation_id == rec.id)
        )).scalar_one_or_none()
        overlay = (await self.db.execute(
            select(RiskOverlayResult).where(RiskOverlayResult.recommendation_id == rec.id)
        )).scalar_one_or_none()

        wt_count = (await self.db.execute(
            select(func.count()).select_from(RecommendationWeight)
            .where(RecommendationWeight.recommendation_id == rec.id)
        )).scalar() or 0

        return {
            "recommendation_id": rec.id,
            "status": rec.status,
            "created_at": rec.created_at,
            "source_feature_set_id": rec.source_feature_set_id,
            "source_signal_run_ids": rec.source_signal_run_ids,
            "model_confidence": rec.model_confidence,
            "data_confidence": rec.data_confidence,
            "operational_confidence": rec.operational_confidence,
            "rationale_summary": rec.rationale_summary,
            "warnings": rec.warnings if isinstance(rec.warnings, list) else [],
            "weight_count": wt_count,
            "selection": {
                "id": sel.id, "included_count": len(sel.included_assets or []),
                "excluded_count": len(sel.excluded_assets or []), "rationale": sel.rationale,
            } if sel else None,
            "allocation": {
                "id": alloc.id, "method": alloc.method,
                "position_count": len(alloc.weights or {}), "rationale": alloc.rationale,
            } if alloc else None,
            "timing": {
                "id": timing.id, "urgency": timing.urgency,
                "horizon_days": timing.horizon_days, "rationale": timing.rationale,
            } if timing else None,
            "risk_overlay": {
                "id": overlay.id, "portfolio_risk_score": overlay.portfolio_risk_score,
                "adjustment_count": len(overlay.adjustments or []), "rationale": overlay.rationale,
            } if overlay else None,
        }

    async def get_status(self) -> dict:
        pipeline_count = (await self.db.execute(
            select(func.count()).select_from(Recommendation)
            .where(Recommendation.source_feature_set_id.is_not(None))
        )).scalar() or 0
        published_count = (await self.db.execute(
            select(func.count()).select_from(Recommendation)
            .where(Recommendation.status.in_(["published", "published_with_warning"]))
        )).scalar() or 0
        latest = await self.get_latest_pipeline_recommendation()
        return {
            "latest_recommendation_id": latest.id if latest else None,
            "latest_status": latest.status if latest else None,
            "latest_created_at": latest.created_at if latest else None,
            "total_pipeline_recommendations": pipeline_count,
            "total_published": published_count,
        }
