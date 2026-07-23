"""Uncertainty tiers that move the decision threshold (phase 6).

The market survey found this to be the most decision-useful mechanic in the
industry, and the clearest gap in FINRLX. Morningstar does not annotate an
answer with an uncertainty label — uncertainty *changes what qualifies*: a
low-uncertainty name needs a 20% discount for five stars, a very-high one needs
50%. Being less sure raises the bar instead of adding a caveat.

FINRLX had confidence values, caveats and capability gates, but confidence
never visibly moved anything. A reader seeing "confidence 0.4" had no way to
know what to do differently.

This module computes a tier from four signals the system already measures, and
returns the thresholds a stance must clear *at that tier*. Nothing here is a
forecast and nothing is calibrated against outcomes — it is a stated policy
that widens the neutral band as evidence weakens, and it says so.

Design rules:
  * Every input is a real measured value; a missing input widens the band
    (fails toward caution) rather than being assumed benign.
  * The cut-points are UI/policy conventions, NOT engine thresholds. They are
    published in the payload so the reader can see the rule being applied,
    the same way the engine's own +0.30/-0.25 are shown on the dial.
  * The base stance is left untouched. This reports what the stance *would* be
    under the widened band, so the effect of uncertainty is visible rather
    than silently applied — a silent change would be a different kind of
    dishonesty.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Engine thresholds this widens from. Mirrors STANCE_BUY_THRESHOLD /
# STANCE_SELL_THRESHOLD in single_ticker_analysis.py.
BASE_CONSTRUCTIVE = 0.30
BASE_CAUTIOUS = -0.25

# Tier -> multiplier on the distance from zero a score must cover.
# 1.0 leaves the engine's own thresholds untouched.
TIER_MULTIPLIER: dict[str, float] = {
    "low": 1.0,
    "medium": 1.35,
    "high": 1.8,
    "very_high": 2.5,
}

TIER_ORDER = ("low", "medium", "high", "very_high")

# Cut-points for each contributing signal. Published in the payload.
CONFIDENCE_WEAK = 0.45          # ensemble confidence below this adds a step
CONFIDENCE_VERY_WEAK = 0.25
DISAGREEMENT_WIDE = 0.60        # spread across engine scores (range -1..1)
DISAGREEMENT_VERY_WIDE = 1.00
MIN_SESSIONS_FOR_FULL_CONFIDENCE = 252  # one trading year


@dataclass(frozen=True)
class UncertaintyAssessment:
    tier: str
    multiplier: float
    constructive_at: float
    cautious_at: float
    reasons: list[str] = field(default_factory=list)
    inputs: dict = field(default_factory=dict)

    def stance_for(self, score: float) -> str:
        """The stance this score earns under the widened band."""
        if score >= self.constructive_at:
            return "constructive"
        if score <= self.cautious_at:
            return "cautious"
        return "neutral"


def _bump(tier_idx: int, steps: int = 1) -> int:
    return min(tier_idx + steps, len(TIER_ORDER) - 1)


def assess_uncertainty(
    *,
    avg_confidence: float | None,
    engine_scores: list[float] | None = None,
    sessions: int | None = None,
    is_stale: bool = False,
) -> UncertaintyAssessment:
    """Grade how much to trust a reading, and widen the band accordingly.

    Each argument is a value the dossier already carries. Passing ``None`` for
    any of them raises the tier: absence of evidence is not evidence that
    conditions are benign.
    """
    idx = 0
    reasons: list[str] = []

    # 1. Ensemble confidence.
    if avg_confidence is None:
        idx = _bump(idx)
        reasons.append("ensemble confidence unavailable")
    elif avg_confidence < CONFIDENCE_VERY_WEAK:
        idx = _bump(idx, 2)
        reasons.append(f"ensemble confidence {avg_confidence:.2f} is very low")
    elif avg_confidence < CONFIDENCE_WEAK:
        idx = _bump(idx)
        reasons.append(f"ensemble confidence {avg_confidence:.2f} is low")

    # 2. Disagreement between engines. A blended score of 0.3 from three
    #    engines that agree is a different object from the same 0.3 produced by
    #    one strongly positive and one strongly negative engine.
    spread: float | None = None
    if engine_scores:
        finite = [s for s in engine_scores if isinstance(s, int | float)]
        if len(finite) >= 2:
            spread = max(finite) - min(finite)
            if spread >= DISAGREEMENT_VERY_WIDE:
                idx = _bump(idx, 2)
                reasons.append(f"engines disagree sharply (spread {spread:.2f})")
            elif spread >= DISAGREEMENT_WIDE:
                idx = _bump(idx)
                reasons.append(f"engines disagree (spread {spread:.2f})")

    # 3. History depth — percentile and validation machinery both need a year.
    if sessions is None:
        idx = _bump(idx)
        reasons.append("history depth unknown")
    elif sessions < MIN_SESSIONS_FOR_FULL_CONFIDENCE:
        idx = _bump(idx)
        reasons.append(
            f"{sessions} sessions of history, under the {MIN_SESSIONS_FOR_FULL_CONFIDENCE} "
            "needed for full-confidence comparisons"
        )

    # 4. Staleness — a reading computed on old bars describes an old market.
    if is_stale:
        idx = _bump(idx)
        reasons.append("underlying market data is stale")

    tier = TIER_ORDER[idx]
    mult = TIER_MULTIPLIER[tier]
    if not reasons:
        reasons.append("all uncertainty inputs within normal range")

    return UncertaintyAssessment(
        tier=tier,
        multiplier=mult,
        constructive_at=round(BASE_CONSTRUCTIVE * mult, 4),
        cautious_at=round(BASE_CAUTIOUS * mult, 4),
        reasons=reasons,
        inputs={
            "avg_confidence": avg_confidence,
            "engine_score_spread": round(spread, 4) if spread is not None else None,
            "sessions": sessions,
            "is_stale": is_stale,
        },
    )


def uncertainty_block(
    *,
    composite_score: float,
    avg_confidence: float | None,
    engine_scores: list[float] | None = None,
    sessions: int | None = None,
    is_stale: bool = False,
) -> dict:
    """Serialisable payload block for the dossier summary.

    `stance_under_uncertainty` is reported alongside the engine's own stance
    rather than replacing it. When the two differ, that difference IS the
    finding — it says the reading is not strong enough to survive its own
    uncertainty — and the reader should see it stated, not applied invisibly.
    """
    a = assess_uncertainty(
        avg_confidence=avg_confidence,
        engine_scores=engine_scores,
        sessions=sessions,
        is_stale=is_stale,
    )
    return {
        "tier": a.tier,
        "multiplier": a.multiplier,
        "thresholds": {
            "base": {"constructive_at": BASE_CONSTRUCTIVE, "cautious_at": BASE_CAUTIOUS},
            "adjusted": {"constructive_at": a.constructive_at, "cautious_at": a.cautious_at},
        },
        "stance_under_uncertainty": a.stance_for(composite_score),
        "reasons": a.reasons,
        "inputs": a.inputs,
        "kind": (
            "policy rule that widens the neutral band as evidence weakens — "
            "not a calibrated probability and not a prediction"
        ),
    }
