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
        "states": [s.__dict__ if hasattr(s, "__dict__") else s for s in states],
        "splits": [list(s) for s in splits],
    }
    with open(out, "w") as f:
        json.dump(payload, f, default=str)
    print(f"exported {len(states)} states, {len(splits)} splits -> {out}")


if __name__ == "__main__":
    main()
