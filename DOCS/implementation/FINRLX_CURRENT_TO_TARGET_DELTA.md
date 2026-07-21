# FINRLX — Current-to-Target Delta (P0 Truth & Safety / EP-1 DecisionPacket)

> Working analysis produced during the P0/EP-1 intake. Every "current capability"
> claim below is backed by inspected code or an executed test. Assumptions are
> marked **[ASSUMPTION]**.

## 1. Baseline pins

| Item | Value |
|---|---|
| Repository | `rotemyoeli/FINRLX` |
| Current branch (at intake) | `main` |
| Current commit | `5767a5c8a56ed5db16616add7544d1b3453a8379` |
| Spec baseline commit | `5767a5c8a56ed5db16616add7544d1b3453a8379` (identical — no drift) |
| Working branch | `feature/p0-truth-safety-foundation` |
| origin/main divergence | `0 / 0` (in sync) |
| Python | 3.11.9 · pydantic 2.10.4 · pydantic-settings 2.7.1 |
| Node | v24.14.0 · npm 11.9.0 |
| Backend deps | `requirements.txt` / `requirements-dev.txt` (pip); ruff + mypy via `pyproject.toml`; pytest via `pytest.ini` |
| Frontend deps | Next.js 0.2.0 workspace, `package.json` (npm), vitest + playwright + tsc |
| CI | `.github/` workflows present (not re-run here; local checks used) |

**No material drift** between spec baseline and current repo: the spec was cut
against the exact commit currently checked out.

## 2. Verified current architecture (inspected)

- **Backend**: FastAPI app (`app/main.py`), routes aggregated in `app/api/router.py`
  (~50 v1 routers). SQLAlchemy async ORM (`app/models/*`), Alembic migrations
  (`backend/migrations`), SQLite for dev/tests, Postgres in prod.
- **Response envelope**: `ApiResponse[T]` with `ResponseMeta` (`app/schemas/common.py`).
- **Auth**: JWT bearer (`app/core/auth.py`, `app/api/auth_deps.py`) with
  `get_current_user` (required) and `get_optional_user` (mixed). Tenant column
  `user_id` exists on `Recommendation` but is **nullable and not enforced** by the
  legacy recommendation read endpoints (verified: `app/api/v1/recommendations.py`
  applies no ownership filter).
- **Feature flags**: env-driven booleans on `Settings` (`app/core/config.py`),
  surfaced read-only at `GET /api/v1/flags` (`app/api/v1/flags.py`). Backend routes
  are **not** hard-gated by flags today (frontend uses them to hide nav). Precedent
  flag that ships dark: `feature_desk_v2` (default `False`).
- **Truth-source services already present** (reused, not rebuilt):
  - `app/services/price_freshness.py` — per-ticker trading-day lag → `fresh|stale|degraded`.
  - `app/services/provenance.py` — tamper-evident input/policy hashes for replay.
  - `app/services/backtest_hygiene.py`, `ml_promotion.py`, `ml_validation.py` — evidence gates.
- **`Recommendation` model** carries: confidence triplet (model/data/operational),
  `data_as_of`, `policy_version_id`, `input_hash`, `policy_hash`, `pipeline_version`,
  `source_feature_set_id`, `source_signal_run_ids`, `warnings`.
- **Existing `decision.py`** (schema + API) is the *pipeline-stage* view
  (selection/allocation/timing/risk-overlay) — **unrelated** to the canonical
  DecisionPacket; no naming collision (new file is `decision_packet.py`).

## 3. Baseline checks executed (pre-change)

| Check | Command | Result |
|---|---|---|
| Focused truth/safety tests | `pytest` (flags, provenance, freshness, backtest-hygiene, auth, healthz, one-price-truth, smoke) | **84 passed** |
| Full backend suite | `pytest -q` | **exit 0 (green)** |
| Backend lint | `ruff check app/schemas app/services app/api` | **clean** |
| Backend types | `mypy` (gate: `app/core/`, `app/schemas/`) | **clean (35 files)** |
| Candidate contract | `pytest tests/test_decision_packet.py` (unmodified) | **12 passed** |

## 4. P0 story status (EP-0 — Baseline, Truth & Security)

| Story | Status | Evidence / note |
|---|---|---|
| **US-P0-01** Repository/runtime inventory | **Implemented** | Machine-readable manifest at admin-only `GET /api/v1/ops/runtime-inventory` (`runtime_inventory.py` + `inventory.py` schema): routes+auth level, flags, provider presence, schema contracts, runtime pins. Tests: `test_p0_runtime_inventory.py`. |
| **US-P0-02** Test baseline | **Verified complete (this slice)** | Full suite green pre- and post-change; focused truth suite recorded above. |
| **US-P0-03** Route authorization matrix | **Audit implemented; enforcement pending decision** | `app/core/route_policy.py` declares an explicit public allowlist + a labeled **auth-debt baseline of 199 method+path entries** (unauthenticated today, should be gated). Audit surfaced in the manifest (`authz`, `unclassified_public_routes`) and gated by `test_p0_route_authz.py` (one-way ratchet: no new unauthenticated route, no baseline growth, no stale entries). **Finding: 210/254 routes are currently public.** Actually auth-gating the 199 needs a product decision on the beta auth model (does the FE send tokens on all calls?). |
| **US-P0-04** Secure web session | **Requires runtime verification** | JWT bearer present; HttpOnly server session / rotation E2E not verified here. |
| **US-P0-05** CSP/web hardening | **Partially implemented** | `app/core/security_headers.py` exists (`test_mvp5_security_headers.py`); full CSP review out of scope this slice. |
| **US-P0-06** Zero-fiction audit | **Partially implemented (advanced here)** | Adapter classifies demo/synthetic/unknown sources and fails them closed; no repo-wide static scan yet. |
| **US-P0-07** Freshness suppression | **Partially implemented (advanced here)** | `price_freshness` reused; stale/degraded/unavailable data blocks packet eligibility with reason codes. |
| **US-P0-08** Readiness endpoint | **Partially implemented** | `data_health` / `healthz` routes exist (`test_mvp7_healthz.py`); unified readiness-with-scope not verified. |
| **US-P0-09** Flag manifest/rollback | **Partially implemented** | Flags surfaced at `/flags`; `decision_packet_v1` added with documented rollback (§8). |
| **US-P0-10** Desk W1 deltas | **Out of scope this slice** | Tracked under `feature_desk_v2`; untouched. |

## 5. DecisionPacket / EP-1 (P1) contract status

- Spec classifies the canonical `DecisionPacket` under **EP-1 / P1** (US-DPK-01..07),
  **not** P0. Adding the three candidate files does **not** complete P0.
- **US-DPK-01 Schema v1** — **Implemented** as contract scaffolding
  (`app/schemas/decision_packet.py`) behind `decision_packet_v1` (default OFF).
- **US-DPK-03 Current adapter** — **Implemented (read-only)**
  (`app/services/decision_packet_adapter.py` + `GET /recommendations/{id}/decision-packets`).
- **US-DPK-02/04/05/06/07** — **Missing** (snapshot manifest, persistence, full
  ETag API, generated TS client, cross-surface equality) — deferred by design.

## 6. Contradictions & risks recorded

1. **Naming vs. classification**: the ZIP is named "P0 DecisionPacket" but the
   delivery spec places DecisionPacket in P1/EP-1 and P0 = Truth & Safety. → We do
   **not** claim P0 completion; packet ships dark as EP-1 scaffolding.
2. **Per-portfolio vs. per-ticker**: `Recommendation` is a portfolio of weights;
   `DecisionPacket` is per-ticker. → Adapter emits **one packet per weighted asset**.
3. **Legacy recommendation read is not user-scoped** (`user_id` nullable, unfiltered).
   → New route adds a fail-closed ownership guard (owned rec → owner-only, else 404)
   without altering legacy endpoints.
4. **SQLite returns naive datetimes** while the packet contract requires tz-aware.
   → Adapter coerces naive→UTC (storage convention), never invents an offset.
5. **Financial-truth risk**: current pipeline has no calibrated forecast, no linked
   reproducible backtest, no prospective validation, no risk frame. → Every packet
   built from today's data is honestly `blocked`/`research_only`; the adapter cannot
   fabricate evidence to reach `ready_for_review`.

## 7. Selected first slice + acceptance tests

**Slice**: Integrate the candidate DecisionPacket contract + truth gate as
read-only scaffolding behind `decision_packet_v1` (default OFF), wired into the
smallest real path (Recommendation → per-ticker packet), advancing US-P0-06/07 and
US-DPK-01/03.

**Acceptance tests (all passing):**
- Candidate contract/gate invariants — `tests/test_decision_packet.py` (12).
- Fail-closed adapter matrix — `tests/test_p1_decision_packet_adapter.py` (12):
  synthetic/demo/unknown source, missing/stale/unavailable freshness, incomplete
  lineage, low/null confidence, naive-timestamp coercion, stance→intent, clean
  data → `research_only` (never `ready_for_review`).
- API flag + auth — `tests/test_p1_decision_packet_api.py` (6): flag off → 404,
  flag on → bundle with explicit outcomes, unknown rec → 404, owner read OK,
  cross-user → 404, anonymous → 404.
- Flag manifest shape — `tests/test_mvp4_feature_flags.py` (updated exact-set).

## 8. Rollback strategy

- The entire surface is dark by default (`feature_decision_packet_v1=False`);
  when off, `GET …/decision-packets` returns 404 and no legacy behavior changes.
- Rollback = leave the flag OFF (or unset `FEATURE_DECISION_PACKET_V1`). Matches
  the spec rollback for `decision_packet_v1`: "return to legacy read while retaining
  new records." No migration, no schema change, no data mutation in this slice.
- Full revert = drop the new files + the 4 additive edits (config/flags/router/test);
  no other module imports them.
