"""LEAP A3 (D45) — FinRL ensemble artifacts: loader + tournament merge.

The E7 research worker trains the ICAIF-2020 ensemble (PPO / A2C / DDPG,
quarterly best-agent selection by rolling validation Sharpe, turbulence
circuit-breaker) and publishes ONE artifact per ticker (schema E.6):

  research/artifacts/finrl_ensemble/{TICKER}.json
  {
    "schema_version": "e6-1",
    "ticker": "NVDA", "generated_at": "...Z",
    "recipe": "icaif2020-ensemble",
    "splits": [[train_end, val_end], ...],        # MUST match the service's
                                                  # walk-forward protocol
    "agents": {
      "rl_ppo":  {"name": "PPO (FinRL ensemble)",
                  "train_sharpe": ..., "val_sharpe": ...,
                  "per_split_val_sharpe": [...]},
      "rl_a2c":  {...}, "rl_ddpg": {...}
    },
    "selection_history": [ {"period": "2025-Q3", "selected": "rl_ppo",
                            "val_sharpe": 1.1, "turbulence_gate": false}, ... ],
    "turbulence_events": [ {"date": "...", "action": "liquidate"} ]
  }

Honesty invariants (all tested):
  - The loader VERIFIES the artifact's splits equal the service's splits for
    this run; mismatched protocols are rejected (protocol_mismatch) — an RL
    agent may never be scored on friendlier windows than the local candidates.
  - Merged rows are re-scored with the SAME formula and the deflation penalty
    recomputed over the ENLARGED candidate count — adding RL legs makes the
    bar higher for everyone, including themselves (D36).
  - Absent artifact => the existing honest queued status; nothing changes.
"""
from __future__ import annotations

import json
import logging
import math
import pathlib

logger = logging.getLogger(__name__)

ARTIFACT_DIR = (
    pathlib.Path(__file__).resolve().parents[3] / "research" / "artifacts" / "finrl_ensemble"
)
SCHEMA_VERSION = "e6-1"
REQUIRED_AGENT_FIELDS = ("name", "train_sharpe", "val_sharpe", "per_split_val_sharpe")


def load_artifact(ticker: str) -> dict | None:
    path = ARTIFACT_DIR / f"{ticker.upper()}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("ensemble artifact unreadable for %s: %s", ticker, exc)
        return None
    if data.get("schema_version") != SCHEMA_VERSION:
        logger.warning("ensemble artifact schema mismatch for %s", ticker)
        return None
    return data


def validate_against_splits(artifact: dict, service_splits: list[tuple[int, int]]) -> str | None:
    """None when valid; otherwise the rejection reason."""
    art_splits = [tuple(x) for x in (artifact.get("splits") or [])]
    if art_splits != [tuple(s) for s in service_splits]:
        return "protocol_mismatch"
    agents = artifact.get("agents") or {}
    if not agents:
        return "no_agents"
    for key, a in agents.items():
        if not all(f in a for f in REQUIRED_AGENT_FIELDS):
            return f"agent_incomplete:{key}"
        if len(a["per_split_val_sharpe"]) != len(art_splits):
            return f"agent_split_count:{key}"
    return None


def merge_rl_candidates(
    ticker: str,
    rows: list[dict],
    service_splits: list[tuple[int, int]],
    n_val_periods: int,
    divergence_lambda: float,
) -> tuple[list[dict], dict]:
    """Merge artifact agents into tournament rows with honest re-scoring.

    Returns (rows_rescored, rl_status). On any gate failing, rows come back
    RESCORED ONLY IF unchanged is impossible — i.e., when nothing merges,
    the original rows are returned untouched.
    """
    artifact = load_artifact(ticker)
    if artifact is None:
        return rows, _queued_status()

    reason = validate_against_splits(artifact, service_splits)
    if reason is not None:
        logger.warning("ensemble artifact rejected for %s: %s", ticker, reason)
        return rows, {
            "status": "artifact_rejected",
            "reason": reason,
            "note": "The research artifact did not match this run's walk-forward "
                    "protocol and was excluded — RL agents are never scored on "
                    "different windows than local candidates.",
        }

    merged = [dict(r) for r in rows]
    for key, a in (artifact.get("agents") or {}).items():
        train_s, val_s = float(a["train_sharpe"]), float(a["val_sharpe"])
        merged.append({
            "key": key,
            "name": a["name"],
            "kind": "rl",
            "description": f"FinRL ensemble agent ({artifact.get('recipe')}), "
                           "trained in the isolated research environment (E7).",
            "train_sharpe": round(train_s, 3),
            "val_sharpe": round(val_s, 3),
            "divergence": round(abs(train_s - val_s), 3),
            "eligible": True,
            "per_split_val_sharpe": [round(v, 3) for v in a["per_split_val_sharpe"]],
            "imported_from_artifact": True,
        })

    # D36: deflation penalty recomputed over the enlarged candidate set.
    n_eligible = len(merged)
    penalty = round(math.sqrt(math.log(max(n_eligible, 2)) / max(n_val_periods, 2)), 4)
    for r in merged:
        r["penalty"] = penalty
        r["score"] = round(
            r["val_sharpe"] - divergence_lambda * r["divergence"] - penalty, 3
        )

    status = {
        "status": "artifact_merged",
        "recipe": artifact.get("recipe"),
        "generated_at": artifact.get("generated_at"),
        "agents": sorted((artifact.get("agents") or {}).keys()),
        "selection_history": artifact.get("selection_history") or [],
        "turbulence_events": artifact.get("turbulence_events") or [],
        "note": "RL agents compete under the same walk-forward protocol and "
                "penalties as every other candidate.",
    }
    return merged, status


def _queued_status() -> dict:
    return {
        "status": "queued_for_research_run",
        "note": "PPO/A2C/DDPG ensemble legs (ICAIF-2020 recipe) train only in "
                "the isolated research environment (operator item E7). When an "
                "artifact is published they join this tournament under the same "
                "protocol and penalties.",
        "candidates": ["rl_ppo", "rl_a2c", "rl_ddpg"],
    }
