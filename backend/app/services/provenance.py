"""Recommendation provenance (Phase MVP-3).

A Recommendation must be replayable: given the same inputs and the same policy,
re-running the pipeline must produce a byte-identical output. This module
computes the tamper-evident hashes that bind a Recommendation to:

  - the SignalOutput rows that fed it (input_hash)
  - the pipeline policy constants in effect at run time (policy_hash)
  - the pipeline version (semver string baked at module load)

Hashes are SHA-256 over canonical JSON (sort_keys=True, separators=(',', ':'))
so byte-identical reconstruction is possible across Python versions/processes.

This module is provider-agnostic and side-effect-free. The pipeline service
calls compute_input_hash / compute_policy_hash and stores the results on
Recommendation. The replay harness re-computes both and asserts equality.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Iterable

# Bump this on any change to the pipeline's deterministic behavior.
PIPELINE_VERSION = "mvp3.0.0"


def _sha256_canonical(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=_json_safe)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _json_safe(o: Any) -> Any:
    """Default encoder for objects json doesn't know about."""
    # datetimes -> ISO 8601
    iso = getattr(o, "isoformat", None)
    if callable(iso):
        return iso()
    if isinstance(o, set):
        return sorted(o)
    return str(o)


def canonical_signal_row(row: Any) -> dict[str, Any]:
    """Project a SignalOutput-shaped object into a stable dict for hashing.

    Accepts either a SignalOutput ORM row or a dict with equivalent keys.
    Only fields that affect the recommendation outcome are hashed; created_at
    and id are excluded so re-runs of the same logical run hash identically.
    """
    if isinstance(row, dict):
        return {
            "signal_run_id": row.get("signal_run_id"),
            "asset_id": row.get("asset_id"),
            "score": row.get("score"),
            "stance": row.get("stance"),
            "confidence": row.get("confidence"),
            "artifacts": row.get("artifacts"),
        }
    return {
        "signal_run_id": getattr(row, "signal_run_id", None),
        "asset_id": getattr(row, "asset_id", None),
        "score": getattr(row, "score", None),
        "stance": getattr(row, "stance", None),
        "confidence": getattr(row, "confidence", None),
        # Artifacts carry "ticker" / "drivers" / "caveats" — they affect the
        # rationale text and aggregate stance, so include them.
        "artifacts": getattr(row, "artifacts", None),
    }


def compute_input_hash(signal_rows: Iterable[Any]) -> str:
    """Order-independent SHA-256 over the signal rows used by the pipeline."""
    canonical = sorted(
        (canonical_signal_row(r) for r in signal_rows),
        key=lambda x: (
            str(x.get("signal_run_id") or ""),
            str(x.get("asset_id") or ""),
        ),
    )
    return _sha256_canonical(canonical)


def compute_policy_hash(policy: dict[str, Any]) -> str:
    """SHA-256 of the policy constants in effect. Order-independent via sort_keys."""
    return _sha256_canonical(policy)


def new_replay_seed() -> str:
    """Generate a per-run replay seed (UUID string).

    Today the pipeline is fully deterministic so the seed is informational.
    Future Monte-Carlo/sampling steps must thread this seed through their RNG.
    """
    return str(uuid.uuid4())


def verify_provenance(
    rec_input_hash: str | None,
    rec_policy_hash: str | None,
    expected_input_hash: str,
    expected_policy_hash: str,
) -> tuple[bool, list[str]]:
    """Compare stored provenance against freshly-computed hashes.

    Returns (ok, mismatches). Use to assert replay determinism in tests and
    to gate operator-facing "is this recommendation still replayable?" UI.
    """
    mismatches: list[str] = []
    if rec_input_hash != expected_input_hash:
        mismatches.append(
            f"input_hash mismatch: stored={rec_input_hash} expected={expected_input_hash}"
        )
    if rec_policy_hash != expected_policy_hash:
        mismatches.append(
            f"policy_hash mismatch: stored={rec_policy_hash} expected={expected_policy_hash}"
        )
    return (not mismatches, mismatches)
