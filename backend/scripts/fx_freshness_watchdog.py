"""Phase FX-4 — FX freshness watchdog entrypoint.

Run manually or on a cron / OP-2 schedule:

    python -m scripts.fx_freshness_watchdog
    python -m scripts.fx_freshness_watchdog --threshold 24

Exits 0 always (the watchdog records incidents in the DB; let OPs decide
what to do with them).
"""
from __future__ import annotations

import argparse
import asyncio

from app.core.database import async_session_factory
from app.services.fx_freshness import (
    DEFAULT_STALE_THRESHOLD_HOURS,
    emit_incidents_if_stale,
    evaluate_freshness,
)


async def _run(threshold_hours: float) -> dict[str, int]:
    async with async_session_factory() as db:
        report = await evaluate_freshness(db, threshold_hours=threshold_hours)
        result = await emit_incidents_if_stale(db, report)
    return {
        **result,
        "evaluated_pairs": len(report.pairs),
        "stale_pairs": len(report.stale_pairs),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Open an Incident per stale FX pair in the local cache.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_STALE_THRESHOLD_HOURS,
        help=f"Hours above which a pair is considered stale (default {DEFAULT_STALE_THRESHOLD_HOURS}).",
    )
    args = parser.parse_args()
    result = asyncio.run(_run(args.threshold))
    print(
        "fx_freshness_watchdog: "
        f"evaluated_pairs={result['evaluated_pairs']} "
        f"stale_pairs={result['stale_pairs']} "
        f"opened={result['opened']} "
        f"skipped_existing={result['skipped_existing']}"
    )


if __name__ == "__main__":
    main()
