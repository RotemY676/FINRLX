# FINRLX — Live Progress Table (Rule 8)

**Legend:** ✅ done · 🟡 done/blocked with reservations (see note) · ⏳ in progress · ⬜ pending
**Updated:** 2026-07-21

---

## Track 0 — Governance infrastructure bootstrap (this request)

| # | Stage / Task | Owner | Gate | Status | Notes |
|---|---|---|---|---|---|
| 0.1 | Inspect repo conventions (DOCS, RESUME, skills) | lead | — | ✅ | No `CLAUDE.md` existed; `DOCS/` is docs home. |
| 0.2 | Root `CLAUDE.md` bootstrap (forces Rule 2) | lead | — | ✅ | Auto-loaded each session. |
| 0.3 | `PROJECT_RULES.md` (the 10 rules) | lead | — | ✅ | Authoritative law file. |
| 0.4 | `SESSION_STATE.md` (crash-recovery memory, Rule 3) | lead | — | ✅ | Live resume point. |
| 0.5 | `AGENT_TEAM.md` (Rule 5) | lead | — | ✅ | Selection method + roster. |
| 0.6 | `COUNCIL.md` (Rule 6) | lead | — | ✅ | Seats + stage gates G0–G4. |
| 0.7 | `WORKFLOW.md` (Rules 7–9 SOP) | lead | — | ✅ | Pipeline + push discipline. |
| 0.8 | `PROGRESS.md` (this table, Rule 8) | lead | — | ✅ | Live table. |
| 0.9 | `README.md` (structure map, Rule 10) | lead | — | ✅ | How it all binds. |
| 0.10 | Commit + push governance layer (Rule 7) | lead | G4 | ✅ | Commit `79f5621` pushed to `main`. |
| 0.11 | Present structure to user, confirm, resume dev | lead | — | ⏳ | Structure presented; awaiting user go-ahead on next track. |

## Track DPK/P1 — DecisionPacket truth-gate (delivered by crashed session, verified on `main`)

| # | Task | Gate | Status | Notes |
|---|---|---|---|---|
| DPK-baseline | Runtime + truth baseline docs (ADR-0001, DELTA, STATUS) | — | ✅ | `bb7b9cb`. |
| DPK-contract | Canonical packet schema + `decision_truth.py` policy | — | ✅ | `1772551` (candidate ZIP adapted to repo conventions). |
| DPK-integrate | Feature-flagged (`decision_packet_v1`, OFF) adapter + API | — | ✅ | `eb03555`. Read-only seam; legacy paths intact. |
| DPK-tests | Fail-closed evidence policy tests (P1 adapter+API) | — | ✅ | `c7fd0dd`. |

## Track P0 — Security/Ops hardening (inherited + this session)

| # | Task | Gate | Status | Notes |
|---|---|---|---|---|
| P0-01 | Runtime inventory manifest (admin-only) | — | ✅ | On `main` (cff56c5). |
| P0-03 i0 | Route authorization matrix + audit ratchet | — | ✅ | On `main` (a8633f3). |
| P0-03 i1 | Auth-gate publication governance mutations (5) | — | ✅ | On `main` (20483af). |
| P0-03 i2 | Auth-gate market-data ingestion (bars/news) | G4 | ✅ | **This session** `28b8bf6`. 39 focused + 1394 full suite green; ruff/mypy clean. Debt 194→192. |
| P0-06 i1 | Zero-fiction static scan + ratchet (`fiction_policy.py`) | G4 | ✅ | **This session** `cb25076`. Surfaced the beta synthetic ingest generators. |
| P0-06 i2 | Fail-closed on synthetic ingest sources (allowlist) | G4 | ✅ | **This session** `52dda91`. Fixed a real fail-open leak: "local" beta data now blocked. 1414 suite green. |
| P0-06 i3 | Label seeded demo endpoints (`/regime`,`/scenario`) | G4 | ✅ | **This session** `ec6e944`. `DEMO_DATA:` in `meta.warnings`. 1418 suite green. |
| P0-07 i1 | Wire `meta.freshness` envelope + `/pricechart` | G4 | ✅ | **This session** `038e71b`. Was never populated (silent-fresh leak). 1423 suite green. |
| P0-07 i2 | Freshness fan-out: `/overview`, `/recommendations/current`, `/autopilot/dossier`, `/autopilot/desk/*` | G4 | ✅ | **2026-07-22.** +2 builders (`from_datetime`, `from_dossier`, fails closed). Desk-status ETag now folds in staleness. 22 focused + **1440 full suite** green. |
| P0-04 | Secure web session — rotation hardening + replay detection | G4 | 🟡 | **2026-07-22.** Fixed latent bug: `replaced_by_id` never persisted (flush-time id) → rotation chain was unlinked. Added replay detection (revokes descendant chain), chain-scoped + cycle-safe. 1443 suite green. **Caveat:** HttpOnly cookie migration deliberately NOT done — contradicts locked Decision 2 (bearer on every call). |
| DEPLOY-01 | `/version` deploy-verification probe (frontend) | G4 | ✅ | **2026-07-22.** Reports live commit/branch/repo from `RAILWAY_GIT_*`. Makes "is the newest push live?" answerable — previously only 200s were observable. |
| P0-08 | Unified readiness endpoint + jobs component | — | ✅ | On `main` (e3ba39a, d1a772d). |

## Remaining P0 work (priority order) — MODE: full autonomous, no check-ins
- ✅ **US-P0-07** — freshness envelope wired across every surface that serves market data: `/pricechart` (i1), plus `/overview`, `/recommendations/current`, `/autopilot/dossier`, `/autopilot/desk/{ticker}/status` and `/autopilot/desk/{ticker}/{section}` (i2).
  - 🟡 **Scope correction:** `/analysis/single-ticker` was on the i1 follow-up list but **cannot carry `meta.freshness`** — it returns a raw `HTMLResponse`, not the `ApiResponse` envelope, so there is no `meta` to populate. Declaring freshness there needs a different mechanism (in-document banner or a response header); logged, not silently dropped.
- 🟡 **US-P0-04** — secure web session. **Rotation + CSRF done**; HttpOnly deliberately deferred.
  - Rotation: hardened with replay detection (a replayed token burns its descendant chain) **and** a latent bug fixed — `replaced_by_id` had never been persisted, so the chain existed only in intent.
  - CSRF: structurally N/A for a bearer-token API (no ambient credentials to ride). The only cookie, Google OAuth `state`, already has HttpOnly + SameSite=Lax + state matching.
  - **HttpOnly cookie session: NOT done, by decision.** It contradicts locked Decision 2 (FE sends a bearer on every call). Revisit only if that product decision is reopened.
- 🟡 **US-P0-05** — CSP / web hardening. **Frontend now sends a CSP + 6 defense-in-depth headers** (`frontend/next.config.js` `headers()`), pinned by `src/__tests__/security-headers.test.ts`.
  - **Audit finding:** the live frontend was serving **zero** security headers while `security_headers.py` claimed it set its own CSP. A documented control that did not exist; comment corrected.
  - **Known limitation (tested, not hidden):** `script-src` still allows `'unsafe-inline'`/`'unsafe-eval'` — the root layout injects an inline theme script and the Next runtime needs eval. Nonce-based hardening via middleware is the follow-up. Everything structural (`frame-ancestors`, `base-uri`, `object-src`, `form-action`, `default-src`, `connect-src`) is enforced.
  - **Trap for whoever touches this next:** `headers()` is evaluated at **build** time into `routes-manifest.json`; `next start` never re-reads it. A build without `NEXT_PUBLIC_API_BASE_URL` therefore emits `connect-src 'self'` and blocks every API call. The origin is pinned with the same fallback `services/api.ts` uses — keep the two in sync.
- 🟡 **US-P0-03 — 192 → 16 (176 routes gated, 92%).** Five batches, 2026-07-23. **Every mutating and operator route is now gated**; what remains is read-only.
  - **Invariant now enforced by test:** no route left in `AUTH_DEBT_BASELINE` can change server state — a `POST`/`PUT`/`PATCH`/`DELETE` reappearing there fails the build.
  - **The last 16 are blocked on a client change, not on effort.** They are exactly the routes the frontend fetches with **no Authorization header** — the Simple Mode front door (`/autopilot/dossier`, `/assets`), the Analyst Desk (`/autopilot/desk/*`), and the read-only research surfaces (`/overview`, `/recommendations/*`, `/pricechart`, `/news`, `/regime`, `/prices/freshness`, `/comparison/current`, `/activity`, `/analysis/single-ticker`, `/autopilot/compare`). Gating them today takes the live product down.
  - **Decision required (product, not engineering):** either the FE attaches a bearer to these calls, or anonymous research is intended and they move to `PUBLIC_ALLOWLIST` with a review note. Until one is chosen the debt cannot honestly reach zero. Pinned by `test_frontend_anonymous_surfaces_are_still_recorded_as_debt` so they cannot be gated by accident.
  - **Pattern to reuse for the remaining batches:** gate at `include_router(..., dependencies=[Depends(get_current_user)])`, not per-endpoint — a route added later to that module is then gated by default instead of failing open when someone forgets.
  - **Test harness is now in place** (this was the expensive part, done once): conftest's shared `client` carries an operator bearer, and `anon_client` is the explicit no-credentials client. ~400 existing call sites keep working untouched; negative tests that pass a forged token are unaffected (httpx gives per-request headers precedence over client defaults).
  - **A shrinking baseline is not evidence.** Each batch must add runtime proof like `test_p0_rl_authz.py` — anonymous ⇒ 401 *and* operator bearer ⇒ not 401 — otherwise entries could simply be deleted from the baseline with nothing actually gated.
  - **Remaining 125 by group:** `models` 15, `paper` 14, `ops` 12, `universes` 10, `engines` 9, `backtests` 6, `policies` 6, `features` 5, `pipeline` 5, then a long tail. `engines`/`features`/`pipeline` carry heavy test-fixture use — expect the most churn there.
- ✅ **US-P0-06** — zero-fiction: static scan + fail-closed synthetic sources + demo labels (i1–i3 done). Follow-up only: demo-flag gating / real regime model (product decision).

## 📍 Phases 1–8 execution status (2026-07-23)

| # | Phase | Status | Evidence |
|---|---|---|---|
| 1 | Truth exposures | ✅ | `/regime` rebuilt on real bars; scenario disclosure renders; fiction scanner gained the `demo-route` detector |
| 2 | Dead indicators wired | ✅ | live: `rsi_14 62.539`, `macd_hist 1.599`, `turbulence 0.211`, all with percentile |
| 3 | RL producer + blend weights | ✅ | import fixed, `episode_returns()` added, fail-closed synthetic guard, weights actually applied |
| 4 | Uncertainty legible | ✅ | split-consistency, threshold proximity, drivers/caveats |
| 5 | Desk v2 gate G-1 | 🟡 | **10/10 e2e green** + found and fixed a real AA contrast failure. G-2/G-4/G-6/G-7 still open — see below |
| 6 | Uncertainty moves the bar | ✅ | `uncertainty.py`; band widens with weak evidence, never narrows (swept by test) |
| 7 | Forward track record | ✅ | capture wired into dossier persist; withholds a rate below 20 directional observations |
| 8 | EP-1 DPK-02 | 🟡 | content-addressed snapshots + honest lineage kinds. **DPK-04/05/06/07 open** |

**Suite:** backend **1593 passed / 6 skipped / 0 failed** · frontend **146 + 10 e2e** · ruff + mypy clean.

### What is NOT done, and why

- **`FEATURE_DESK_V2` stays OFF.** SPEC-04 requires G-1…G-7 in one run. G-2 needs 84 frames
  reviewed against three reference standards — that is a **human visual judgment** the spec
  exists to force. G-4 (Lighthouse), G-6 (ten-ticker production reality with data-health green)
  and G-7 (a real Railway flag flip + rollback rehearsal) also need an operator. Flipping the
  flag on G-1 alone would bypass the gate the spec was written to impose.
- **EP-1 cannot complete on engineering alone.** No calibrated forecast, reproducible backtest or
  prospective validation exists upstream, so **no packet can reach `ready_for_review`** — by
  design. Phase 7 started accumulating the only input that fixes this, and it accrues in
  wall-clock time, not in commits.
- **RL still produces no artifact.** The producer can now *start*; running it needs the research
  container (torch/SB3 are deliberately not backend deps). That is operator item **E7**.

## 🗺️ Road to product — remaining phases (authored 2026-07-23)

**Where the project actually is.** MVP-0…MVP-8 closed 2026-05-20; the post-MVP A/B tracks
(Universe, Ops, Policy, Integrations, Risk, News, Saved views) and the UX track are shipped
and their flags are ON. Verified this session: C1 (F821) clean, C6 done (FastAPI 0.118,
Next 15, React 19). So "MVP" in the original sense is behind us — what separates today from
a product a stranger can rely on is **three features still dark behind flags**, **four P0
residuals**, and **launch operations**.

**Three flags still OFF** — this is the honest definition of remaining scope:
`feature_desk_v2`, `feature_decision_packet_v1`, `feature_operator_console`.

| # | Phase | Scope | Blocked by | Exit condition |
|---|---|---|---|---|
| **0** | **Decisions** | D1 FE-bearer vs public-allowlist · D2 HttpOnly vs bearer session | **User** | Both answered; P0-03 + P0-04 can close |
| **1** | **Desk v2 → prod** | Gates G-1…G-7 (e2e · 84 frames · axe+keyboard · Lighthouse · zero-fiction+drawer · ten-ticker prod reality · rollback rehearsal) | none | `FEATURE_DESK_V2=true` in prod |
| **2** | **P0 residuals** | P0-05 nonce CSP (drop `unsafe-inline`) · P0-06 demo-flag gating / real regime model · P0-07 freshness on `/analysis/single-ticker` (header or in-doc banner) | P0-06 needs a product call | P0 track fully ✅, no 🟡 |
| **3** | **EP-1 DecisionPacket** | DPK-02 snapshot manifest → DPK-04 immutable persistence → DPK-05 ETag/history API → DPK-06 generated TS client → DPK-07 cross-surface equality | DPK-02 first (unblocks 04) | `decision_packet_v1=true`; a packet can reach `ready_for_review` honestly |
| **4** | **Operator console** | Wire + verify the console behind `feature_operator_console` | Phase 1 patterns | flag ON |
| **5** | **Launch ops** | Sentry + PostHog DSNs · CI re-enable (billing) · E1 rotate PAT (treat as compromised) · E7 torch research worker · E8 Finnhub social tier · beta invites | E1/E7/E8 need user (secrets/paid) | Beta cohort onboarded |

**Sequencing rationale.** Phase 1 first: the Desk is the product's main surface, its work is
already done, and only the gate run stands between it and users. Phase 3 is the largest and
most valuable — DecisionPacket is the contract the whole "truth-first" thesis rests on, and
it stays dark until it can be honest, so it is deliberately *after* the P0 residuals rather
than before. Phase 5 is last because it costs money and secrets, not engineering.

**Honest note on Phase 3.** No calibrated forecast, reproducible backtest, prospective
validation or risk frame exists upstream yet, so **no packet can currently reach
`ready_for_review` — by design, not a bug**. Phase 3 is not "turn on the flag"; it is
building the evidence chain that makes the flag meaningful.

## Backlog / other candidate tracks
- ⬜ Browser phase (`DOCS/handoff/CLAUDE_CODE_HANDOFF_DESK_W1.md`): e2e matrix, screenshots, gates G-1..G-7, then flip `FEATURE_DESK_V2`.
- ⬜ Operator items: E1 (rotate PAT — treat as compromised), E7 (torch worker), E8 (Finnhub social tier).

## Carried caveat
- 🟡 `research/finrlx_cpu/*.json` registries are dirty from a local test run (UUID/timestamp churn) — deliberately **not committed**. Restore or ignore at will.

---
_This table is the live view. `SESSION_STATE.md` holds the narrative resume detail._
