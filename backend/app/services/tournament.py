"""Program LEAP S4 — Autopilot model tournament core (decisions D35–D37).

Pure, DB-free primitives so the statistical machinery is independently
testable; the autopilot pipeline (S2 integration) feeds it bars/features and
persists the resulting scoreboard into dossiers.

Pieces:
  walk_forward_splits(dates, n_splits)      expanding train/validation splits
                                            over trading sessions (F2 calendar
                                            already applied by the caller when
                                            building `dates`)
  sharpe(returns)                           annualized daily-return Sharpe
  score_candidate(train_rets, val_rets, m)  D36 score = validation Sharpe
                                            − divergence penalty
                                            − multiple-testing penalty(m)
  run_tournament(candidates, splits, ...)   evaluates every candidate on every
                                            split, aggregates, applies D36
                                            tie-break (simpler wins), returns a
                                            full scoreboard (D37: the why ships
                                            with the winner)

Honesty invariants:
  - Every candidate's train-vs-validation divergence is computed and shown.
  - The multiple-testing penalty grows with the number of candidates tried
    (deflated-Sharpe-style sqrt(2 ln m) haircut), so adding candidates cannot
    silently inflate the winner.
  - Ties inside SCORE_EPS resolve toward the simpler complexity class:
    heuristic < ml < rl (D36).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Sequence

TRADING_DAYS_PER_YEAR = 252
SCORE_EPS = 1e-6
COMPLEXITY_ORDER = {"heuristic": 0, "ml": 1, "rl": 2}
DIVERGENCE_WEIGHT = 0.5  # D36: penalty per unit of (train - validation) Sharpe gap

__all__ = [
    "CandidateResult",
    "TournamentResult",
    "walk_forward_splits",
    "sharpe",
    "score_candidate",
    "run_tournament",
]


# ── splits ──────────────────────────────────────────────────────────────────


def walk_forward_splits(
    dates: Sequence[date], n_splits: int = 3, min_train: int = 60
) -> list[tuple[list[date], list[date]]]:
    """Expanding-window walk-forward splits over an ordered session list.

    The tail of the series is divided into `n_splits` contiguous validation
    blocks; each split trains on everything strictly before its block.
    Guarantees: no validation date ever appears in its own training window,
    training windows only grow, and every training window has at least
    `min_train` sessions (splits that can't are dropped).
    """
    if n_splits < 1:
        raise ValueError("n_splits must be >= 1")
    ordered = list(dates)
    if sorted(ordered) != ordered:
        raise ValueError("dates must be ascending")
    val_total = len(ordered) - min_train
    if val_total < n_splits:
        return []
    block = val_total // n_splits
    splits: list[tuple[list[date], list[date]]] = []
    for k in range(n_splits):
        val_start = min_train + k * block
        val_end = len(ordered) if k == n_splits - 1 else val_start + block
        train = ordered[:val_start]
        val = ordered[val_start:val_end]
        if len(train) >= min_train and val:
            splits.append((train, val))
    return splits


# ── scoring (D36) ───────────────────────────────────────────────────────────


def sharpe(returns: Sequence[float]) -> float:
    """Annualized Sharpe of daily returns (rf=0); 0.0 for degenerate input."""
    n = len(returns)
    if n < 2:
        return 0.0
    mean = math.fsum(returns) / n
    var = math.fsum((r - mean) ** 2 for r in returns) / (n - 1)
    # Constant/near-constant series have no meaningful Sharpe. The epsilon is
    # relative to the mean's scale so float-summation residue (which differs
    # across Python versions: 3.12 sum() is compensated, 3.11 is not) can
    # never masquerade as real variance and explode the ratio.
    if var <= (1e-9 * max(abs(mean), 1e-12)) ** 2:
        return 0.0
    return (mean / math.sqrt(var)) * math.sqrt(TRADING_DAYS_PER_YEAR)


def multiple_testing_penalty(n_candidates: int) -> float:
    """Deflated-Sharpe-style haircut: grows ~sqrt(2 ln m) with candidates tried."""
    if n_candidates <= 1:
        return 0.0
    return 0.5 * math.sqrt(2.0 * math.log(n_candidates))


def score_candidate(
    train_returns: Sequence[float],
    validation_returns: Sequence[float],
    n_candidates: int,
) -> dict:
    """D36 score decomposition for one candidate over one (or pooled) split."""
    s_train = sharpe(train_returns)
    s_val = sharpe(validation_returns)
    divergence = max(s_train - s_val, 0.0)  # only overfit-direction gaps penalized
    div_penalty = DIVERGENCE_WEIGHT * divergence
    mt_penalty = multiple_testing_penalty(n_candidates)
    return {
        "train_sharpe": round(s_train, 4),
        "validation_sharpe": round(s_val, 4),
        "divergence": round(divergence, 4),
        "divergence_penalty": round(div_penalty, 4),
        "multiple_testing_penalty": round(mt_penalty, 4),
        "score": round(s_val - div_penalty - mt_penalty, 4),
    }


# ── tournament ──────────────────────────────────────────────────────────────

# A candidate maps a list of session dates to the daily strategy returns it
# realizes over those dates; the harness calls it once per split per window.
CandidateFn = Callable[[list[date]], list[float]]


@dataclass
class CandidateResult:
    name: str
    complexity: str  # heuristic | ml | rl
    per_split: list[dict] = field(default_factory=list)
    aggregate: dict = field(default_factory=dict)
    status: str = "evaluated"  # evaluated | failed | skipped


@dataclass
class TournamentResult:
    candidates: list[CandidateResult]
    winner: str | None
    rationale: str
    n_splits: int
    disclaimers: tuple[str, ...] = (
        "Research analysis, not investment advice.",
        "Walk-forward validation on historical data; past performance does not "
        "predict future results.",
        "Scores include divergence and multiple-testing penalties; see the "
        "decomposition per candidate.",
    )


def run_tournament(
    candidates: dict[str, tuple[str, CandidateFn]],
    splits: list[tuple[list[date], list[date]]],
) -> TournamentResult:
    """Evaluate every candidate on every split; pick the D36 winner.

    `candidates`: name -> (complexity, fn). A candidate that raises is marked
    failed (never crashes the tournament) and cannot win.
    """
    if not splits:
        return TournamentResult(
            candidates=[], winner=None, n_splits=0,
            rationale="insufficient history for walk-forward validation",
        )
    m = len(candidates)
    results: list[CandidateResult] = []
    for name, (complexity, fn) in candidates.items():
        cr = CandidateResult(name=name, complexity=complexity)
        train_pool: list[float] = []
        val_pool: list[float] = []
        try:
            for train_dates, val_dates in splits:
                tr = list(fn(list(train_dates)))
                vr = list(fn(list(val_dates)))
                cr.per_split.append(score_candidate(tr, vr, m))
                train_pool += tr
                val_pool += vr
            cr.aggregate = score_candidate(train_pool, val_pool, m)
        except Exception as exc:  # noqa: BLE001 — candidate boundary
            cr.status = "failed"
            cr.aggregate = {"error": str(exc)[:200], "score": float("-inf")}
        results.append(cr)

    viable = [c for c in results if c.status == "evaluated"]
    if not viable:
        return TournamentResult(
            candidates=results, winner=None, n_splits=len(splits),
            rationale="all candidates failed evaluation",
        )
    best_score = max(c.aggregate["score"] for c in viable)
    contenders = [c for c in viable if best_score - c.aggregate["score"] <= SCORE_EPS]
    winner = min(contenders, key=lambda c: COMPLEXITY_ORDER.get(c.complexity, 99))
    tie_note = (
        f"; tie among {len(contenders)} resolved toward simpler complexity"
        if len(contenders) > 1
        else ""
    )
    rationale = (
        f"{winner.name} scored {winner.aggregate['score']} "
        f"(validation Sharpe {winner.aggregate['validation_sharpe']}, "
        f"divergence penalty {winner.aggregate['divergence_penalty']}, "
        f"multiple-testing penalty {winner.aggregate['multiple_testing_penalty']} "
        f"across {m} candidates){tie_note}"
    )
    return TournamentResult(
        candidates=results, winner=winner.name,
        n_splits=len(splits), rationale=rationale,
    )
