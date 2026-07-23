"""Final research verdict from the model tournament (model-lab dashboard).

The dashboard's job is to turn a real, walk-forward model comparison into one
legible read: on the strength of the models, does the evidence lean
constructive, cautious, or is it inconclusive? This is NOT advice and NOT a
prediction — it is a transparent rule over real validation scores, and every
input that moved it is shown.

Three honesty rules shape the logic:

  * If a passive benchmark (Buy & Hold) wins the tournament, NO active model
    beat simply holding. The honest read is "no active edge found", not a
    constructive signal — an active recommendation would overstate what the
    models showed. This is the single most important truthful output here.

  * The uncertainty tier (phase 6) pulls the verdict toward inconclusive as
    evidence weakens, the same way it widens the stance band elsewhere.

  * A winner that only won some splits is weaker than one that won them all;
    consistency gates how strong the verdict may be.

Vocabulary is the product's research language (constructive / cautious /
inconclusive) — never advice verbs. The caller renders a hard disclaimer.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Kinds that represent passive exposure rather than an active model edge.
PASSIVE_KINDS = {"benchmark"}
PASSIVE_KEYS = {"buy_hold"}


@dataclass(frozen=True)
class ModelVerdict:
    verdict: str  # "constructive" | "cautious" | "inconclusive"
    headline: str
    reasons: list[str] = field(default_factory=list)
    models_compared: int = 0
    winner_name: str | None = None
    winner_score: float | None = None
    winner_is_passive: bool = False
    rl_participated: bool = False
    disclaimer: str = (
        "Research synthesis of a walk-forward model comparison — not investment "
        "advice, not a prediction, and not a probability of future return."
    )


def _winner_is_passive(winner: dict) -> bool:
    return (
        winner.get("kind") in PASSIVE_KINDS
        or winner.get("key") in PASSIVE_KEYS
    )


def _split_consistency(winner: dict) -> tuple[int, int]:
    splits = winner.get("per_split_val_sharpe") or []
    positive = sum(1 for s in splits if isinstance(s, int | float) and s > 0)
    return positive, len(splits)


def decide_from_tournament(
    tournament: dict,
    *,
    uncertainty_tier: str | None = None,
) -> ModelVerdict:
    """Reduce a real tournament to one honest research verdict.

    `tournament` is the `sections.model_insight` block: candidates, winner,
    n_splits, and the RL leg status.
    """
    candidates = tournament.get("candidates") or []
    winner = tournament.get("winner")
    rl = tournament.get("rl") or {}
    rl_participated = rl.get("status") == "artifact_merged"

    # No validated winner — the tournament could not run honestly.
    if not winner or tournament.get("status") != "complete":
        return ModelVerdict(
            verdict="inconclusive",
            headline="The model tournament could not produce a validated winner.",
            reasons=[tournament.get("note") or "insufficient history to validate candidates"],
            models_compared=len(candidates),
            rl_participated=rl_participated,
        )

    score = winner.get("score")
    passive = _winner_is_passive(winner)
    pos, n = _split_consistency(winner)
    reasons: list[str] = []

    # Rule 1 — a passive winner means no active edge, regardless of its score.
    if passive:
        reasons.append(
            f"The best-validated candidate is a passive benchmark "
            f"({winner.get('name')}); no active model beat simply holding."
        )
        verdict = "inconclusive"
        headline = "No active model beat passive holding — no active edge found."
        return ModelVerdict(
            verdict=verdict, headline=headline, reasons=reasons,
            models_compared=len(candidates), winner_name=winner.get("name"),
            winner_score=score, winner_is_passive=True,
            rl_participated=rl_participated,
        )

    # Rule 2 — a negative validated score is a cautious read.
    if isinstance(score, int | float) and score <= 0:
        reasons.append(f"The winning model's validation score is {score} (≤ 0).")
        return ModelVerdict(
            verdict="cautious",
            headline="Even the best model failed to validate positively.",
            reasons=reasons, models_compared=len(candidates),
            winner_name=winner.get("name"), winner_score=score,
            rl_participated=rl_participated,
        )

    # An active model validated positively. How strong depends on consistency
    # and uncertainty.
    reasons.append(
        f"{winner.get('name')} led {len(candidates)} candidates with a "
        f"validation score of {score} after the overfitting and multiple-testing penalties."
    )
    if n:
        reasons.append(f"It was positive in {pos} of {n} walk-forward splits.")

    weak_consistency = n and pos < n
    weak_uncertainty = uncertainty_tier in {"high", "very_high"}

    if weak_consistency or weak_uncertainty:
        if weak_consistency:
            reasons.append("The edge is not consistent across every split.")
        if weak_uncertainty:
            reasons.append(f"Overall uncertainty is {uncertainty_tier.replace('_', ' ')}.")
        verdict = "inconclusive"
        headline = "An active model validated, but the edge is not robust."
    else:
        verdict = "constructive"
        headline = "An active model validated positively and consistently."

    if rl_participated:
        reasons.append("Reinforcement-learning agents competed under the same protocol.")

    return ModelVerdict(
        verdict=verdict, headline=headline, reasons=reasons,
        models_compared=len(candidates), winner_name=winner.get("name"),
        winner_score=score, rl_participated=rl_participated,
    )


def verdict_block(tournament: dict, *, uncertainty_tier: str | None = None) -> dict:
    v = decide_from_tournament(tournament, uncertainty_tier=uncertainty_tier)
    return {
        "verdict": v.verdict,
        "headline": v.headline,
        "reasons": v.reasons,
        "models_compared": v.models_compared,
        "winner_name": v.winner_name,
        "winner_score": v.winner_score,
        "winner_is_passive": v.winner_is_passive,
        "rl_participated": v.rl_participated,
        "disclaimer": v.disclaimer,
    }
