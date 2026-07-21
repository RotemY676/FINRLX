# FINRLX — Implementation Status: DecisionPacket truth-gate scaffolding

- **Date**: 2026-07-21
- **Base commit**: `5767a5c8a56ed5db16616add7544d1b3453a8379` (`main`)
- **Branch**: `feature/p0-truth-safety-foundation`
- **Scope**: EP-1/US-DPK-01 + US-DPK-03 contract scaffolding; advances P0 US-P0-06/07.
  **Not** a completion of P0. **No** live trading, alerts, notifications, broker
  execution, or production deployment.

## Specification requirements addressed

| ID | What |
|---|---|
| US-DPK-01 | Canonical `DecisionPacket` schema v1 + `TruthGate` + `DecisionTruthPolicy` (contract). |
| US-DPK-03 | Read-only adapter: `Recommendation` → per-ticker `DecisionPacket` in the smallest real path. |
| US-P0-06 | Zero-fiction: demo/synthetic/unknown-provenance market data fails closed. |
| US-P0-07 | Freshness suppression: stale/degraded/unavailable data blocks packet eligibility with reason codes. |
| US-P0-02 | Repeatable test baseline recorded (full suite green pre & post). |
| US-P0-09 | New flag with documented, tested rollback. |

## Files changed

**New**
- `backend/app/schemas/decision_packet.py` — packet contract (from candidate, adapted; + `DecisionPacketBundle` response wrapper).
- `backend/app/services/decision_truth.py` — `evaluate_truth_gate` + `build_decision_packet` (from candidate, unmodified logic).
- `backend/app/services/decision_packet_adapter.py` — pure read-only projection (new).
- `backend/app/api/v1/decision_packets.py` — flag-gated read-only endpoint (new).
- `backend/tests/test_decision_packet.py` — candidate contract tests (unmodified).
- `backend/tests/test_p1_decision_packet_adapter.py` — fail-closed matrix (new, 12).
- `backend/tests/test_p1_decision_packet_api.py` — flag + auth integration (new, 6).
- `docs/implementation/FINRLX_CURRENT_TO_TARGET_DELTA.md`, this file, and `docs/adr/ADR-0001-decision-packet-truth-gate.md`.

**Edited (additive only)**
- `backend/app/core/config.py` — `feature_decision_packet_v1: bool = False`.
- `backend/app/api/v1/flags.py` — expose `decision_packet_v1`.
- `backend/app/api/router.py` — register the new router.
- `backend/tests/test_mvp4_feature_flags.py` — add the new key to the exact-set assertion.

## Architectural decisions

- Reused existing `price_freshness` + `Recommendation` lineage fields instead of a
  competing source of truth; the truth gate is derived from evidence, never
  caller-asserted (see ADR-0001).
- The adapter is a **pure function** (no DB/network) so fail-closed policy is unit-tested
  directly; the endpoint does the I/O and hands plain values in.
- One packet per weighted asset (portfolio → per-ticker) with a deterministic
  `packet_id = dpk:{rec_id}:{ticker}` flowing through the path.

## Accepted deviations from the candidate package

- Candidate `decision_packet.py` / `decision_truth.py` / `test_decision_packet.py`
  copied **without logic changes** (already repo-convention-compliant, mypy-gate clean,
  passed against pydantic 2.10.4). Added only a `DecisionPacketBundle` response wrapper.
- Candidate did not include an integration seam; we added the adapter + endpoint rather
  than leaving three isolated files (per the real-integration requirement).

## Feature-flag behavior

- `feature_decision_packet_v1` (env `FEATURE_DECISION_PACKET_V1`) default **False**.
- **OFF**: `GET /api/v1/recommendations/{id}/decision-packets` → **404**; legacy
  recommendation reads unchanged; `/flags` reports `decision_packet_v1: false`.
- **ON (dev/test only)**: returns `ApiResponse[DecisionPacketBundle]` with per-packet
  `gate.outcome` ∈ {`blocked`,`research_only`,`ready_for_review`}. With current data,
  outcomes are `blocked`/`research_only` only — never `ready_for_review`.

## Security review performed

- New route uses `get_optional_user`; an **owned** recommendation is owner-only —
  cross-user and anonymous access to an owned rec return **404** (existence not
  disclosed). Unowned (legacy/global) recs remain readable, matching existing behavior.
- Negative tests: cross-user 404, anonymous-on-owned 404, unknown rec 404.
- No provider keys, model paths, stack traces, or config leaked in responses.

## Tests executed (exact commands & results)

| Command | Result |
|---|---|
| `pytest tests/test_decision_packet.py` | 12 passed |
| `pytest tests/test_p1_decision_packet_adapter.py` | 12 passed |
| `pytest tests/test_p1_decision_packet_api.py` | 6 passed |
| `pytest tests/test_mvp4_feature_flags.py` | passed (exact-set updated) |
| `pytest -q` (full backend) | **1365 passed, 2 skipped, 0 failed** (~594s) |
| `ruff check` (new + touched files) | clean |
| `mypy` (gate: core + schemas) | clean (36 files) |
| `npm run typecheck` (frontend) | clean |
| `npm run test:ci` (frontend) | 87 passed (14 files) |
| `npm run build` (frontend) | see PR/commit evidence |

## Baseline vs. newly introduced failures

- Pre-change full suite: **exit 0 (green)**. Post-change full suite: **1365 passed,
  2 skipped, 0 failed**. **No new failures introduced.** The 2 skips are pre-existing.

## Rollback instructions

1. Fastest: keep `FEATURE_DECISION_PACKET_V1` unset/false → surface is 404, zero
   behavior change. (Matches spec rollback: "return to legacy read while retaining
   new records.")
2. Full revert: delete the 6 new backend files and revert the 4 additive edits. No
   migration or data change was made, so revert is clean.

## Known limitations

- Read-only projection only; no persistence, no ETag/history API, no generated TS client
  (US-DPK-02/04/05/06/07 remain open).
- `is_demo`/`is_synthetic` classification is source-token heuristic; a canonical
  provider-provenance registry (US-DPK-02) would replace it.
- No calibrated forecast, reproducible backtest, prospective validation, or risk frame
  exists upstream yet, so no packet can be `ready_for_review` — by design, not a bug.

## Remaining P0 stories (priority order)

1. US-P0-03 Route authorization matrix (repo-wide) — highest safety leverage.
2. US-P0-06 Zero-fiction static scan across production paths (beyond this adapter).
3. US-P0-08 Unified readiness endpoint with affected scope.
4. US-P0-04 Secure web session (HttpOnly/rotation/CSRF E2E).
5. US-P0-01 Machine-readable runtime/route/flag/provider manifest.

## Why DecisionPacket remains disabled

The truth gate is only meaningful once P0 truth/safety foundations (provenance,
readiness, route-auth matrix, snapshot manifest) exist. Shipping it dark lets the
contract and gate be reviewed and tested without implying P0/P1 completion or
surfacing any eligible decision from incomplete evidence.

## Recommended next implementation slice

**US-DPK-02 Snapshot manifest** — introduce `DataSnapshot`/`FeatureSnapshot` IDs with
content hashes and cutoff, then feed real `data_snapshot_id`/`feature_snapshot_id` into
the adapter's lineage. It unblocks honest lineage completeness and is the prerequisite
for US-DPK-04 (immutable persistence) and any future target-range surface.
