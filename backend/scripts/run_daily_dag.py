"""Phase OP-2 — daily DAG runner.

Invoked by a Railway cron / external scheduler:

    python -m scripts.run_daily_dag

Each job in ``app.jobs.daily_dag.DAILY_DAG`` runs in order, with its
own JobRun row for audit.
"""
from __future__ import annotations

import asyncio

from app.core.database import async_session_factory
from app.jobs.daily_dag import run_daily_dag


async def _run() -> dict:
    async with async_session_factory() as db:
        return await run_daily_dag(db, triggered_by="cron")


def main() -> None:
    result = asyncio.run(_run())
    print(
        f"daily_dag: jobs_total={result['jobs_total']} "
        f"completed={len(result['completed'])} "
        f"failed={len(result['failed'])}"
    )
    for f in result["failed"]:
        print(f"  FAILED: {f}")


if __name__ == "__main__":
    main()
