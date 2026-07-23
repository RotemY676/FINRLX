"""US-DPK-02 — content-addressed snapshot IDs for packet lineage.

`DecisionLineage` has always declared `data_snapshot_id` and
`feature_snapshot_id`, and the adapter has always emitted `None` for both. A
packet could therefore say what it concluded but not *which* body of data it
concluded it from, which makes the lineage unverifiable and blocks DPK-04
(immutable persistence): there is nothing stable to persist against.

A snapshot ID here is a content hash, not a surrogate key. Two runs over the
same bars produce the same ID on any machine; one changed close produces a
different one. That is the property that makes lineage checkable rather than
merely recorded — and it is the same discipline `provenance.py` already uses
for `input_hash`/`policy_hash` (SHA-256 over canonical JSON), reused
deliberately so packets and recommendations hash the same way.

Cutoff is part of the identity. The same rows observed with a later cutoff are
a different snapshot, because a cutoff is a claim about what was knowable at
the time.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from datetime import date, datetime
from typing import Any

SNAPSHOT_ALGO = "sha256-canonical-v1"
# Short enough to read in a UI, long enough that collisions are not a concern
# at any plausible corpus size.
_ID_LEN = 16


def _json_safe(o: Any) -> Any:
    iso = getattr(o, "isoformat", None)
    if callable(iso):
        return iso()
    if isinstance(o, set):
        return sorted(o)
    return str(o)


def _canonical_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), default=_json_safe
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _fingerprint(kind: str, cutoff: date | datetime | None, body: Any) -> str:
    digest = _canonical_hash({"kind": kind, "cutoff": cutoff, "body": body})
    return f"{kind}:{digest[:_ID_LEN]}"


def canonical_bar_row(row: Any) -> dict:
    """The identity-bearing fields of one market bar.

    Deliberately excludes surrogate ids and ingestion timestamps: re-ingesting
    the same market day must not change the snapshot. `source` IS included —
    the same close from a different provider is a different evidentiary claim,
    and the zero-fiction allowlist depends on that distinction.
    """
    get = (lambda k: row.get(k)) if isinstance(row, Mapping) else (lambda k: getattr(row, k, None))
    return {
        "ticker": get("ticker"),
        "bar_date": get("bar_date"),
        "close": get("close"),
        "source": get("source"),
    }


def compute_data_snapshot_id(
    bars: Iterable[Any], *, cutoff: date | datetime | None = None
) -> str | None:
    """Content-address the market data a decision was computed from.

    Returns None for an empty set rather than the hash of nothing — a packet
    with no data must carry no snapshot id, not a valid-looking one.
    """
    rows = [canonical_bar_row(b) for b in bars]
    rows = [r for r in rows if r["ticker"] and r["bar_date"] is not None]
    if not rows:
        return None
    rows.sort(key=lambda r: (str(r["ticker"]), str(r["bar_date"])))
    return _fingerprint("data", cutoff, rows)


def canonical_feature_row(row: Any) -> dict:
    get = (lambda k: row.get(k)) if isinstance(row, Mapping) else (lambda k: getattr(row, k, None))
    return {
        "asset_id": get("asset_id"),
        "feature_key": get("feature_key") or get("key"),
        "value": get("value"),
        "quality": get("quality") or get("status"),
    }


def compute_feature_snapshot_id(
    features: Iterable[Any],
    *,
    cutoff: date | datetime | None = None,
    definitions_version: str | None = None,
) -> str | None:
    """Content-address the computed features.

    `definitions_version` participates: the same inputs under a changed feature
    definition are not the same features, and treating them as identical would
    let a definition change pass unnoticed through the lineage.
    """
    rows = [canonical_feature_row(f) for f in features]
    rows = [r for r in rows if r["feature_key"]]
    if not rows:
        return None
    rows.sort(key=lambda r: (str(r["asset_id"]), str(r["feature_key"])))
    return _fingerprint(
        "feat", cutoff, {"definitions_version": definitions_version, "rows": rows}
    )


def snapshot_manifest(
    *,
    bars: Iterable[Any] | None = None,
    features: Iterable[Any] | None = None,
    cutoff: date | datetime | None = None,
    definitions_version: str | None = None,
) -> dict:
    """Both ids plus the inputs that produced them, for display and audit."""
    data_id = compute_data_snapshot_id(bars or [], cutoff=cutoff)
    feat_id = compute_feature_snapshot_id(
        features or [], cutoff=cutoff, definitions_version=definitions_version
    )
    return {
        "algo": SNAPSHOT_ALGO,
        "cutoff": cutoff,
        "data_snapshot_id": data_id,
        "feature_snapshot_id": feat_id,
        "definitions_version": definitions_version,
        # Counts make an empty snapshot legible instead of just null.
        "bar_count": len(list(bars)) if isinstance(bars, list | tuple) else None,
    }
