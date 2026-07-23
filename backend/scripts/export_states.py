#!/usr/bin/env python3
"""LEAP A3 — export a ticker's rebalance states + service walk-forward splits
for the E7 ensemble runner, guaranteeing protocol identity with production.

Usage: python scripts/export_states.py NVDA /tmp/nvda_states.json
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, ".")

from app.services.autopilot import (  # noqa: E402
    HISTORY_DAYS_DEFAULT,
    _generate_weekly_rebalances,
    fetch_history,
    fetch_news,
    precompute_rebalance_states,
    walk_forward_splits,
)


def _env_rows(states: list) -> list[dict]:
    """Rows the research env consumes, computed from the real states.

    The env reads `engine_score` and `realized_return` per row; a
    RebalanceState carries neither directly (and its `window` field is a whole
    Bars object). Dumping `state.__dict__` therefore produced rows the env
    could not read — every one hit the synthetic fallback and the fail-closed
    guard rejected the run, which is why no artifact was ever produced.

    Both values here are real:
      * engine_score   = the ensemble composite score AT that state.
      * realized_return = the actual forward return from this state to the
        next. The final state has no successor, so it gets 0.0 and the env's
        last step contributes nothing rather than inventing a return.
    """
    rows: list[dict] = []
    for i, s in enumerate(states):
        nxt = states[i + 1] if i + 1 < len(states) else None
        fwd = ((nxt.price - s.price) / s.price) if (nxt and s.price) else 0.0
        rows.append({
            "date": s.date.isoformat(),
            "price": round(s.price, 6),
            "engine_score": round(float(s.composite.get("composite_score", 0.0)), 6),
            "realized_return": round(float(fwd), 8),
        })
    return rows


def main() -> None:
    ticker, out = sys.argv[1].upper(), sys.argv[2]
    bars = fetch_history(ticker, HISTORY_DAYS_DEFAULT)
    news, _ = fetch_news(ticker)
    start = bars.dates[max(0, min(60, len(bars.dates) - 1))]
    rebalances = _generate_weekly_rebalances(start, bars.dates[-1])
    states = precompute_rebalance_states(bars, news, rebalances)
    splits = walk_forward_splits(len(states))
    payload = {
        "ticker": ticker,
        "states": _env_rows(states),
        "splits": [list(s) for s in splits],
        "latest_bar": bars.dates[-1].isoformat(),
    }
    with open(out, "w") as f:
        json.dump(payload, f, default=str)
    print(f"exported {len(states)} states, {len(splits)} splits -> {out}")


if __name__ == "__main__":
    main()
