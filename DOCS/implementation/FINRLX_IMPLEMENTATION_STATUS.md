# FINRLX — Implementation Status: DecisionPacket truth-gate scaffolding

> **Slice 8 (2026-07-21, on `main`) — US-P0-06 synthetic-source fail-closed (increment 2).**
> Closed a real zero-fiction **leak** the increment-1 scan surfaced. The beta
> ingests deterministic synthetic bars/news under source "local"; downstream
> `decision_packet_adapter._classify_source` used a *denylist* of synthetic
> tokens, so "local" (and any nonempty unknown label) was classified NOT
> synthetic → fabricated random-walk prices could back an eligible decision.
> The code's own comment already promised "unknown provenance is treated as
> non-real", but the implementation only failed closed on an *empty* label.
> Fix: `_classify_source` is now an **allowlist** — only `yfinance`/`chain`
> (the two live-fetch branches in `ingest.py`) are real; everything else is
> `is_synthetic` and fails closed, honoring the P0 rule that no field may
> silently default to a pass. `is_demo` is retained for the more precise reason
> code. Test: `test_p0_synthetic_source_failclosed.py` (real providers pass;
> local/local_deterministic/test/fixture/unknown/empty/None fail closed; demo
> flagged demo+synthetic; allowlist == ingest's real providers). Verify: 46
> focused green (incl. all P1 adapter/API/packet tests, no regression); full
> backend suite **1414 passed / 2 skipped**; ruff + mypy clean.
> Reversible: revert this commit to restore the denylist.
>
> **Slice 7 (2026-07-21, on `main`) — US-P0-06 zero-fiction static scan (increment 1).**
> Added `app/core/fiction_policy.py`: a pure AST/text scan of the serving paths
> (`app/api`, `app/services`) that flags fabrication primitives — any
> `random`/`numpy.random` draw, and `TODO/FIXME` markers admitting fake/mock/
> placeholder/synthetic data. Mirrors the `route_policy.py` ratchet: a reviewed,
> justified baseline (`KNOWN_FICTION_SITES`) that may only shrink, plus a guard
> test (`test_p0_fiction_scan.py`) asserting the current surface exactly equals
> the baseline (no new site; no stale entry). Baseline = 6 sites: 2 non-serving
> (rl test-agent, offline research stub) + 2 pairs of labeled-synthetic beta
> market-data generators in `ingest.py` (`_generate_bars`/`_generate_news`). The
> scan **surfaced the ingest generators**, which no prior audit had enumerated as
> fiction sites. Honest scope: this forward-locks the fabrication surface; it
> does NOT yet prove ingest synthetic data is failed-closed downstream — that
> ingest→`DataTruth.is_synthetic` linkage is increment 2 (next). Verify: 4/4
> guard tests green; ruff + mypy clean.
>
> **Slice 6 (2026-07-21, on `main`) — US-P0-03 enforcement increment 2 (market-data ingestion).**
> Auth-gated `POST /api/v1/ingest/bars` and `POST /api/v1/ingest/news` with
> `get_current_user`. Injecting bars/news is a zero-fiction control surface —
> an anonymous caller must never write market data. Both routes removed from the
> `AUTH_DEBT_BASELINE` ledger (debt 194→192). A new invariant test
> `test_p0_route_authz.py::test_baseline_entries_are_still_public` forces
> removal-on-gating so a now-authenticated route can never be left stale in the
> debt ledger. Tests: `test_p0_ingest_authz.py` (anonymous → 401 for bars+news);
> operator-override `autouse` fixtures added to `test_phase4a_ingestion.py` and
> `test_phase4b_features.py` (both post to the now-gated endpoints as setup).
> Same FE-safe selection pattern as increment 1 (0 anonymous FE references).
> Verify: focused 39/39 green; full backend suite 1394 passed / 2 skipped;
> ruff + mypy(app/core) clean.
>
> **Slice 5 (2026-07-21, on `main`) — US-P0-08 unified readiness endpoint.**
> Admin-only `GET /api/v1/ops/readiness` (`app/services/readiness.py`,
> `app/schemas/readiness.py`, `app/api/v1/ops_readiness.py`) composes market-data
> freshness, FX freshness, and provider readiness into one report: per-component
> status (ready/degraded/unavailable) + affected scope, and an overall verdict =
> worst component. Fail-closed: each evaluator is guarded so a raising component
> becomes `unavailable`, never silently `ready`. Tests: `test_p0_readiness.py`
> (admin gate, shape, seed market-data-ready-but-fx-unavailable, injected-failure
> → unavailable). Model/job/alert components are a follow-up.
>
> **Slice 4 (2026-07-21, on `main`) — US-P0-03 enforcement increment 1.**
> Auth-gated the 5 publication governance mutations (stage/approve/publish/
> defer/suppress) with `get_current_user` — they change what is published to
> users and must never be anonymous. Chosen because a frontend-usage analysis
> showed the core `apiFetch` sends no bearer token, so only routes the FE never
> calls anonymously are safe to gate; these have 0 FE references. Debt baseline
> 199→194, required routes 43→48, `unclassified` still 0. Tests:
> `test_p0_publication_authz.py` (real-token 401/pass, parametrized over all 5)
> + dependency-override fixtures added to the 2 workflow test files that use
> publish as setup. Pipeline/engines/features gating deferred (used as setup in
> ~40 test files each). Next increments follow the same FE-safe pattern.
>
> **Slice 3 (2026-07-21, on `main`) — US-P0-03 Route authorization matrix (audit).**
> `app/core/route_policy.py` makes every route's auth posture explicit: an
> intentionally-public allowlist (11) + a **labeled auth-debt baseline (199
> method+path entries)** — routes unauthenticated today that should be gated.
> The runtime manifest now carries an `authz` split (allowed/debt/unclassified)
> and `unclassified_public_routes`; `tests/test_p0_route_authz.py` enforces a
> one-way ratchet (unclassified must be empty → no new unauthenticated route can
> merge; baseline may only shrink; no stale entries). **Material finding:
> 210/254 routes are currently unauthenticated** (incl. recommendations, paper,
> publication, policies, ops, rl). This slice records + regression-locks the gap
> honestly; *actually* auth-gating the 199 is a follow-up needing a product
> decision on the beta auth model (whether the FE sends a bearer token on every
> call). No route behavior changed in this slice.
>
> **Slice 2 (2026-07-21, on `main`) — US-P0-01 Repository/runtime inventory.**
> Added an admin-only machine-readable manifest at `GET /api/v1/ops/runtime-inventory`
> (`app/services/runtime_inventory.py`, `app/schemas/inventory.py`,
> `app/api/v1/ops_inventory.py`) enumerating routes with their real authorization
> level (derived from the dependency graph), feature flags with live values,
> provider **presence** (booleans only — never secrets or the DB URL), registered
> schema contracts, and runtime pins (app/pipeline/python versions, DB dialect,
> Railway commit SHA when present). Restricted to the established `admin` role
> (401 anon / 403 non-admin / 200 admin). Tests: `tests/test_p0_runtime_inventory.py`
> (5) incl. an explicit no-secret-leakage assertion. Merged and deployed directly on
> `main` per owner request; feature-flag posture unchanged. Slice 1 detail follows.

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
