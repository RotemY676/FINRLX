"""RL baseline agent placeholders.

Phase 7A: lightweight agents for offline simulation. No neural networks, no training.
"""
import random


def heuristic_baseline_agent(state: dict, policy_constraints: dict) -> dict:
    """Produce target weights using deterministic engine signal scores.

    Methodology: score-proportional allocation, constrained by policy rules.
    This is NOT an RL-trained agent — it's a baseline heuristic.
    """
    assets = state.get("assets", [])
    if not assets:
        return {"target_weights": {}, "cash_weight": 1.0, "action_type": "no_op"}

    position_cap = policy_constraints.get("position_cap_max", 0.15)
    cash_floor = policy_constraints.get("cash_floor", 0.05)
    max_invested = policy_constraints.get("max_invested", 0.95)

    # Use engine scores if available, else equal weight
    raw = {}
    for a in assets:
        ticker = a.get("ticker", "?")
        score = a.get("engine_score", 0.5)
        raw[ticker] = max(score, 0.001)

    total_raw = sum(raw.values())
    if total_raw <= 0:
        total_raw = 1.0

    weights = {}
    for ticker, score in raw.items():
        w = (score / total_raw) * max_invested
        w = min(w, position_cap)
        weights[ticker] = round(w, 4)

    # Normalize if over budget
    total = sum(weights.values())
    if total > max_invested:
        scale = max_invested / total
        weights = {t: round(w * scale, 4) for t, w in weights.items()}

    cash = round(max(cash_floor, 1.0 - sum(weights.values())), 4)

    return {"target_weights": weights, "cash_weight": cash, "action_type": "rebalance"}


def random_valid_agent(state: dict, policy_constraints: dict) -> dict:
    """Produce random but valid target weights within policy constraints.

    This agent exists only to test the environment's constraint validation.
    """
    assets = state.get("assets", [])
    if not assets:
        return {"target_weights": {}, "cash_weight": 1.0, "action_type": "no_op"}

    position_cap = policy_constraints.get("position_cap_max", 0.15)
    cash_floor = policy_constraints.get("cash_floor", 0.05)
    max_invested = policy_constraints.get("max_invested", 0.95)

    weights = {}
    remaining = max_invested
    tickers = [a.get("ticker", "?") for a in assets]
    random.shuffle(tickers)

    for ticker in tickers:
        if remaining <= 0:
            break
        w = round(random.uniform(0.01, min(position_cap, remaining)), 4)
        weights[ticker] = w
        remaining -= w

    cash = round(max(cash_floor, 1.0 - sum(weights.values())), 4)

    return {"target_weights": weights, "cash_weight": cash, "action_type": "rebalance"}


AGENTS = {
    "heuristic_baseline": heuristic_baseline_agent,
    "random_valid": random_valid_agent,
}
