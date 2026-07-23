# FINRLX — SESSION STATE (Crash-Recovery Resume Point)

> **Rule 3.** This is the live continuation memory. On any restart, read this FIRST.
> Update it after every user command and every meaningful dev step. Never let it go stale.
> Times are absolute (project date reference: 2026-07-21).

---

## 🔴 RESUME HERE (most recent first)

### Entry — 2026-07-22 · US-P0-07 i2 shipped (freshness fan-out) + `/version` deploy probe
- **User request:** review `DOCS/governance/`, resume the interrupted dev process and run it autonomously to completion; also prove comprehensively that deploys flow through the new `RotemY676` repo and that the live site at `frontend-production-7e8b1.up.railway.app` actually updates.
- **US-P0-07 i2 — freshness now declared on every envelope surface that serves market data:**
  - New builders in `app/services/freshness_state.py`: `freshness_state_from_datetime` (recommendations store `data_as_of` as a datetime) and `freshness_state_from_dossier` (reads the dossier's own `freshness.latest_bar`). Both **fail closed** — missing/`None`/malformed input is stale, never silently fresh.
  - Wired: `/overview`, `/recommendations/current` (both branches + the no-rec branch), `/autopilot/dossier`, `/autopilot/desk/{ticker}/status`, `/autopilot/desk/{ticker}/{section}`. The three autopilot routes return raw dict envelopes (not `ApiResponse`), so `meta.freshness` was added to those dicts directly.
  - **Red-team hardening:** desk-status previously ETag'd on `body["fingerprint"]` alone, so a dossier that went stale without changing content would keep answering `304` and leave the client displaying a "fresh" reading forever. Staleness is now folded into the ETag; a pre-i2 ETag no longer matches, forcing one re-fetch.
- **🟡 Scope correction (do not re-attempt blindly):** `/analysis/single-ticker` was listed as an i2 target but **structurally cannot carry `meta.freshness`** — it returns raw `HTMLResponse`, not the `ApiResponse` envelope. Needs an in-document banner or response header instead. Logged in `PROGRESS.md`, not silently dropped.
- **Evidence (truth-first):** 22 focused PASS; **clean full backend suite 1440 passed / 2 skipped / 0 failed** in 10m45s; `ruff check app` clean; `mypy app/core` clean; frontend **91 vitest PASS**, `tsc --noEmit` clean, `next build` OK. Baseline reconciliation: documented baseline 1423 + 17 new tests in `test_p0_freshness_envelope.py` (5 → 22) = 1440 exactly.
- **⚠️ Process note for future sessions — do NOT run two backend suites concurrently.** An earlier run reported 5 failures in `test_phase8i2_*` / `test_phase8j1_*` with `PermissionError [WinError 5]`. Cause: two pytest runs contending over the **real** `research/finrlx_cpu/*.json` registry files (the DB is in-memory, but those registries are on disk and shared). All 70 PASS in isolation; the clean serial run is green. Not a code defect.
- **`/version` deploy-verification probe (new, `frontend/src/app/version/route.ts`):** returns the live `commit` / `branch` / `repo` / `deploymentId` from the `RAILWAY_GIT_*` runtime vars, `no-store`. Deliberately **outside `/api/*`** because `next.config.js` rewrites that prefix to the backend and would shadow it. This closes the exact observability gap from earlier today: `GET /` returning 200 proves *a* build is up, not that the newest commit is live — which is how a missing deployment trigger hid behind healthy 200s.
- **✅ DEPLOY CHAIN PROVEN AT THE APPLICATION LAYER (2026-07-22 22:09).** Push `bf3c41b` → both services `SUCCESS@bf3c41b` → live site `GET /version` returns `commit=bf3c41b…, repo=RotemY676/FINRLX, branch=main`, **byte-identical to local HEAD**. Next build id changed `EsfEujlieF-Aq4JnKmQZh` → `SXySWjAnbGoDQE0b65Xag`, and `/version` went 404 → 200 (the route did not exist in the previous build) — two independent signals that the site content actually changed, not just that a healthy old build kept answering 200.
  - **Shipped code observably live:** production `GET /api/v1/overview` now returns `meta.freshness = {is_stale: true, staleness_reason: "latest session 2026-04-24 is 60 trading day(s) behind expected 2026-07-22 (degraded)"}`. Worth noting: **production market data really is ~60 trading days stale**, and before this slice the API served that silently as implicitly fresh. US-P0-07 is doing exactly what it was written for.

### Entry — 2026-07-23 · Desk engine dials replaced with an explorable lane rail
- **User report:** the six dials in the desk verdict band "don't look good, aren't intuitive, you can't understand anything from them, and you can't click anything to get detail."
- **Confirmed at source, and it was worse than cosmetic.** `EngineDial` was a 30×30 quarter-arc whose *only* affordance was an HTML `title` tooltip — invisible on touch, unreachable by keyboard. It never said **what a lane measured**, never said **why** it held its state, and rendered closed enum codes like `E7_GATED` raw at the reader.
- **Replaced** with `EngineStatusRail`: each lane is a real `<button>` that expands a reasoned panel — what the lane measures → what the state means → **the server's `reason` verbatim** → the detail code translated to plain language → scope/freshness → a jump link to that panel. Six `DetailCode` values and three `DialState` values now have written explanations in the copy deck (`lib/deskCopy.ts`, the repo's single surface for Desk v2 strings).
- **Contracts deliberately preserved** (the old component was carrying real safety properties):
  - closed-enum `assertNever` — an unknown state is still a **compile-time** error, never a runtime guess (SPEC-02 R3-T1);
  - **NFR-4, never colour alone** — the ring *shape* differs per state (full / gapped+tick / dashed+slash) *and* the state is spelled out in text;
  - `data-testid="dial-<id>"`, `data-state` and the `deskCopy.dialAria` label, so all **18 original desk tests pass untouched**.
- **Visual language:** moved off the separate `deskTokens` hex palette onto the site's own `globals.css` tokens, so the desk stops looking like a different product. Added a deliberately slow "breathe" on live rings (2.8s) — six of these sit in a sticky header, and anything faster competes with the numbers; the global `prefers-reduced-motion` block neutralises it.
- **A guard against the original sin:** a test asserts *every* value of the closed `DetailCode` enum has copy, so adding a code cannot put an opaque token back in front of the reader.
- **Evidence:** 12 new tests; frontend **127 PASS / 19 files**; `tsc --noEmit` clean; `next build` exit 0.

### Entry — 2026-07-23 · US-P0-03 batch 1 — RL surface gated (auth debt 192 → 125)
- **Shipped:** all four RL routers (`rl`, `rl_training`, `rl_benchmark`, `rl_finrlx`) are auth-gated at the `include_router` level. That is **67 of the 192** debt routes — training runs, artifact import, dataset export, the experiment registry: endpoints that mutate models and burn real compute, previously reachable anonymously.
- **Why router-level, not per-endpoint:** a route added to those modules later is now gated by default. Per-endpoint dependencies fail open the moment someone forgets one — which is exactly how a 192-route debt accumulates.
- **The expensive part (done once, reusable for every remaining batch):** the suite had **~417 call sites** written against open RL routes. Rewriting them all would have been enormous churn for zero extra coverage, so conftest's shared `client` now carries an operator bearer and a new **`anon_client`** is the explicit no-credentials client.
  - This does **not** defang the negative tests: httpx gives per-request headers precedence over client defaults, so tests passing a forged/tampered token still exercise the reject path unchanged. Verified, not assumed.
  - All **15 anonymity tests** were migrated to `anon_client` (each failed first for the right reason, then passed). Also deleted a local unauthenticated `client` fixture in `test_phase8n2a_registry_metadata_mirror.py` that was shadowing conftest and started 401-ing.
- **Runtime proof, not a shrinking number:** `tests/test_p0_rl_authz.py` asserts 7 representative RL routes return **401 anonymously** *and* that a genuine operator bearer is **not** rejected. Without this, "debt went down" could just mean the baseline entries were deleted.
- **Evidence:** **full suite 1458 passed / 2 skipped / 0 failed**; `ruff check app` clean; `mypy app/core` clean. Debt confirmed at **125**.
- **NEXT (autonomous):** US-P0-03 batch 2 — `models` (15), `paper` (14), `ops` (12), `universes` (10) using the same pattern. Leave `engines`/`features`/`pipeline` for later: heaviest test-fixture use.

### Entry — 2026-07-23 · Detail-screen visuals + iPhone/iPad pass (+ CSP font hotfix)
- **User instruction:** never stop for approval again — the Council is the approving authority (Rule 11 reaffirmed). Plus: make the detail screen carry impressive, relevant dynamic graphics, and ensure iPhone/iPad browsing works.
- **🔴 REGRESSION I CAUSED AND FIXED (`3925713`):** the US-P0-05 CSP blocked **every web font in production**. `globals.css` line 1 `@import`s Inter Tight / Fraunces / JetBrains Mono from `fonts.googleapis.com` (which pulls woff2 from `fonts.gstatic.com`), and the CSP allowed neither. My post-deploy verification checked HTTP 200 + page title and passed — **a CSP regression degrades quietly instead of breaking the page**. Now allowed, with a regression test that reads `globals.css` and asserts the CSP covers the origins it depends on. Self-hosting via `next/font` is the better end state (removes the third-party dependency entirely) — logged as follow-up.
- **Detail-screen visuals** (`components/simple/DossierVisuals.tsx`, wired into `/` and `/simple`):
  - **`EngineVotes`** — the significant find: the dossier has **always** sent per-engine `score`/`confidence`/`stance` at `sections.technical.engines`, and the frontend never even declared the field. Readers saw a verdict with no way to see how it was reached — a unanimous ensemble and a split one produce the same composite. Now every engine's vote is drawn on one shared −1…+1 axis with confidence encoded.
  - **`EnsembleDial`** — composite score on its real scale with the engine's **actual** thresholds (+0.30 / −0.25) drawn as zones, so proximity to a category change is visible. Constants mirror `single_ticker_analysis.py`; a test pins them so drift is caught.
  - **`PriceArea`** — replaces the recharts chart, which used `type="monotone"` and therefore **interpolated prices between sessions that never traded**. New one is point-to-point with real extremes marked.
  - **`SentimentSplit`** — proportional 7-day headline mix from the real counts.
  - Honesty rules pinned by test: empty/malformed input renders **nothing** rather than a plausible shape; a single price point draws no trend; non-finite closes are dropped, not plotted as zero.
- **iPhone / iPad:** `vh` → `dvh` across **11 sites**. On iOS Safari `vh` resolves against the *largest* viewport, so a `100vh`/`h-screen` column is taller than the visible area while the address bar shows — and in the `overflow-hidden` app shell the final row was unreachable. Added safe-area padding to `SimpleShell`, which opted into `viewport-fit=cover` (content painting under the notch/home indicator) without ever applying insets. Simple-shell nav links raised to the 44pt floor — they are `<Link>`s, which the touch-target lint does not scan (it only walks `<button>`). All guarded by a new `ios-viewport.lint.test.ts`.
- **Accessibility:** `role="img"` + descriptive aria-labels on every chart, `prefers-reduced-motion` honoured (animations become instant), theme tokens only so dark mode and the WCAG-tuned palette apply automatically.
- **Evidence:** frontend **115 PASS / 18 files** (27 new); `tsc --noEmit` clean; `next build` exit 0.
- **NEXT (autonomous):** US-P0-03 bulk route gating (192 `AUTH_DEBT_BASELINE` routes → zero).

### Entry — 2026-07-22 · US-P0-05 shipped (CSP / web hardening) — documented control didn't exist
- **Audit finding (measured on the live sites, not read from source):** the backend sends all 7 security headers; the **browser-facing frontend sent ZERO** — no CSP, no `X-Frame-Options`, no HSTS. Meanwhile `app/core/security_headers.py` stated "the frontend (Next.js) sets its own CSP via next.config.js / meta tags". `next.config.js` had no `headers()` at all. **The control was documented but never existed** — corrected the comment so it now describes reality.
- **Shipped:** `frontend/next.config.js` `headers()` sends a CSP plus `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Strict-Transport-Security`, `Permissions-Policy`, `Cross-Origin-Opener-Policy` on `/:path*`. Pinned by `frontend/src/__tests__/security-headers.test.ts` (8 tests) — a comment is not a control, a test is.
- **🔴 SELF-DoS CAUGHT BEFORE SHIPPING (important, read before editing the CSP):** `headers()` is evaluated at **BUILD** time and baked into `.next/routes-manifest.json`; `next start` never re-reads it. Proved empirically — built without `NEXT_PUBLIC_API_BASE_URL`, started *with* it, and the app still emitted `connect-src 'self'`, which would have **blocked every browser→API call and taken production down**. Fixed by pinning the same hardcoded fallback `src/services/api.ts` already uses (`https://backend-production-aab8.up.railway.app`); the two must stay in sync. Regression test rebuilds the config with the env var deleted.
- **🟡 Known limitation, tested rather than hidden:** `script-src` still allows `'unsafe-inline'`/`'unsafe-eval'` (inline theme script in the root layout + Next runtime eval). A nonce-based policy needs middleware plumbing — that is the follow-up. Everything structural is enforced: `frame-ancestors 'none'`, `base-uri 'self'`, `object-src 'none'`, `form-action 'self'`, `default-src 'self'`, scoped `connect-src`.
- **Also caught:** a build-breaking `eslint-disable` in my own test referencing a rule absent from the project config — `next build` treats it as an Error. Caught locally; would have failed the Railway deploy.
- **Evidence:** 8 new header tests; frontend **99 vitest PASS** (16 files); `tsc --noEmit` clean; `next build` exit 0; backend header tests 4 PASS; `ruff check app` clean. Backend change is comment-only.
- **NEXT (autonomous):** US-P0-03 bulk route gating (192 `AUTH_DEBT_BASELINE` routes → zero), per the locked beta auth model (FE sends a bearer on every call).

### Entry — 2026-07-22 · US-P0-04 shipped (session hardening) — with a latent bug found
- **Latent bug fixed (pre-existing, silent):** `_issue_token_pair` linked `parent.replaced_by_id = child.id` **before the child was flushed**. `RefreshToken.id` is a Python-side `default=gen_uuid` applied at INSERT, so the attribute was still `None` — verified directly. Every rotation had therefore persisted `replaced_by_id = NULL`: the rotation chain the code and docstring claimed to record **never existed**, making token lineage unauditable. Fixed with a flush before linking.
- **Replay detection added (OAuth 2.0 Security BCP §4.14.2):** presenting an already-rotated refresh token now revokes the entire descendant chain, not just that request. Rejecting only the replayed token left the legitimately-issued child alive — i.e. the thief kept a working session. Verified **chain-scoped** (a second device/session survives) and **cycle-safe** (a crafted `replaced_by_id` loop terminates instead of hanging the endpoint).
- **🟡 HttpOnly deliberately NOT done.** US-P0-04's title includes HttpOnly cookies, but migrating there contradicts **locked Decision 2** (FE sends a bearer on every call). Recorded as a decision, not an omission — revisit only if that product decision is reopened. CSRF is structurally N/A for a bearer API; the one cookie (Google OAuth `state`) already has HttpOnly + SameSite=Lax + state matching.
- **Evidence:** 31 focused auth/oauth PASS; **full suite 1443 passed / 2 skipped / 0 failed**; `ruff check app` clean; `mypy app/core` clean.
- **NEXT (autonomous, no approval):** US-P0-05 (CSP / web hardening review), then US-P0-03 bulk gating (192 debt routes → zero).

### Entry — 2026-07-22 · Migrated the deploy chain to the NEW GitHub repo (RotemY676/FINRLX)
- **User request:** verify which GitHub the repo points at; connect to Railway CLI and point the FINRL-X project at the **new** git address; ensure deploys flow new-git → existing Railway.
- **⚠️ Correction to my first pass in this session (recorded for truth):** I initially concluded `RotemY676/FINRLX` did not exist, because `git ls-remote` returned `Repository not found`. That was a **404 masking an authorization failure** — GitHub hides repos the credential can't access. The repo is real. Acting on that wrong conclusion I removed the remote pointing at it, repointed `main` at the old repo, and pushed `b7887f5` to the **old** repo. All three were reversed. **Lesson: never read a GitHub 404 as non-existence without an anonymous re-check.**
- **The two repos:**
  - **NEW / canonical:** `github.com/RotemY676/FINRLX` — created 2026-07-22 15:54:15 UTC, **public**, not a fork, full 374-commit history, `main` @ `b4f900c`.
  - **OLD / retired:** `github.com/rotemyoeli/FINRLX` — private, `main` @ `b7887f5`.
- **Railway repointed via GraphQL `serviceConnect`** (the CLI has *no* command for source repo; the CLI OAuth token in `~/.railway/config.json` → `user.accessToken` works against `https://backboard.railway.com/graphql/v2`, even though the `githubRepos` query returns Not Authorized). Project `FINRL-X` `3f8432e2-…`, env `production` `f8e70246-…`:
  - `FinRL-X` (frontend) `35d09d3f-…` → `RotemY676/FINRLX` @ `main`, root `/frontend`, `frontend-production-7e8b1.up.railway.app`
  - `backend` `509b0240-…` → `RotemY676/FINRLX` @ `main`, root `/backend`, `backend-production-aab8.up.railway.app`, health `/healthz`
  - `postgres` `9c298164-…` — image-based, untouched.
  - **`rootDirectory` survived the reconnect** on both (verified `/frontend`, `/backend`) — this was the main breakage risk.
- **Exclusivity locked (user instruction, 2026-07-22):** the project now works **only** against `RotemY676/FINRLX`. Codified as **Rule 12** in `PROJECT_RULES.md` + the `CLAUDE.md` summary. The `old-rotemyoeli` remote was **removed**; `origin` = `RotemY676/FINRLX` is the sole remote.
- **Before removing the old remote I checked its 6 branches:** `main` + 4 feature branches (`desk/w1-core`, `leap/F0-bootstrap`, `leap/L0-program-plan`, `leap/S7b-pro-migration`) were all already **merged into main**. One was not: `railway/fix-deploy-d8676d` (`899ce31`, a `railway-app[bot]` ESLint fix from 2026-05-01, 4 admin files) — preserved as local branch **`archive/railway-fix-deploy-d8676d`** so nothing is lost. It is stale (main is ~289 files past it, frontend builds green) — drop it unless a reason surfaces.
- **✅ RESOLVED — push access granted.** `rotemyoeli` was added as a collaborator on `RotemY676/FINRLX` (`push: true`, `admin: false`). The three stranded governance commits were pushed: `origin/main` moved `b4f900c → 8f8a2f2` (`b7887f5`, `8c6f352`, `8f8a2f2`). Local `main` == `origin/main`.
- **🟡 DECIDED — repo stays PUBLIC for now (user, 2026-07-22).** The earlier recommendation to flip it private is **withdrawn — do not raise it again unless the user asks.** Standing consequence, recorded once so it is not re-litigated: the full 374-commit history is world-readable, so anything sensitive ever committed is exposed and should be rotated on its own schedule; and **no secret may ever be committed to this repo** — all secrets belong in Railway environment variables only. Changing visibility needs admin on `RotemY676`, which `rotemyoeli` does not have.
- **🐛 ROOT CAUSE FOUND + FIXED — `serviceConnect` does not create the webhook trigger.** After the repo repoint, pushes `8f8a2f2` and `f838594` produced **no deploy at all** (services sat on `b4f900c` for 5+ min). Querying `project.services.…repoTriggers` returned **NO REPO TRIGGER** on every service: `serviceConnect` sets `source.repo` but leaves the service with no push trigger, so the repo looks correctly wired in the UI while auto-deploy is silently dead.
  - **Fix:** `deploymentTriggerCreate(input: {projectId, environmentId, serviceId, provider:"github", repository:"RotemY676/FINRLX", branch:"main"})` — one per git-backed service. Created `886d94e4…` (FinRL-X) and `60bfaa09…` (backend); both verified present.
  - `rootDirectory` was deliberately **omitted** from the triggers to preserve the previous behaviour (every push to `main` rebuilds both services, including docs-only commits). Set it per-trigger if you later want path-filtered builds.
  - **Lesson for any future Railway repoint: `serviceConnect` alone is NOT enough — always verify `repoTriggers` is non-empty and prove auto-deploy with a real push.**
- **✅ CHAIN PROVEN END-TO-END (2026-07-22 19:25 local).** Push of `11f6247` to `RotemY676/FINRLX` triggered a webhook deploy on both services **within seconds** (no manual action): `BUILDING → SUCCESS@11f6247` on both, settled in ~90s. `GET /healthz` → **200**, frontend `GET /` → **200**, both serving `11f6247`. Sole remote is `origin` = `RotemY676/FINRLX`; local `main` == `origin/main`. **The migration is complete and verified.**
- **Standing rule from here:** deploy path is `git push origin main` (→ `RotemY676/FINRLX`) → Railway auto-deploys both services. Never `railway up` (uploads the local tree, bypasses git). Do not push to `old-rotemyoeli`.
- **NEXT:** unblock the 4 items above, then resume US-P0-07 follow-ups (see entry below).

### Entry — 2026-07-21 · US-P0-07 i1 shipped (freshness envelope)
- **Shipped:** `038e71b` — `app/services/freshness_state.py` + `make_meta(freshness=...)` + `/pricechart` wiring. `meta.freshness` was never populated (silent-fresh leak); now declared. Full suite **1423 passed / 2 skipped**; ruff/mypy clean.
- **NEXT (autonomous, no approval):** US-P0-07 follow-ups (wire freshness into `/autopilot/dossier`, `/autopilot/desk/*`, `/analysis/single-ticker`, `/recommendations/current`, `/overview`), then **US-P0-04** (secure web session), **US-P0-05** (CSP), then **US-P0-03 bulk gating** (192 debt routes → zero, per decided auth model). Registries `research/finrlx_cpu/*.json` remain dirty by design.

### Entry — 2026-07-21 · Two directional decisions locked
- **Decision 1 — Execution mode:** FULL AUTONOMOUS, no more check-ins. Run US-P0-07 → US-P0-04 → US-P0-05 back-to-back, Council-gated, commit+push each, stop only for real emergencies. Do NOT ask the user again.
- **Decision 2 — Beta auth model:** the FE sends a bearer on EVERY call → **gate everything**. The remaining ~192 `AUTH_DEBT_BASELINE` routes may all be auth-gated (US-P0-03 unparked). Memory: `project_beta_auth_model`.
- **Work queue (in order):** US-P0-07 freshness suppression → US-P0-04 secure web session → US-P0-05 CSP → US-P0-03 bulk route-gating toward zero debt.
- **NEXT action:** begin US-P0-07 (freshness suppression audit). No approval needed.

### Entry — 2026-07-21 · Autonomous mandate + US-P0-06 delivered (i1–i3)
- **User grant:** Rule 11 — Council approves all stage transitions; do NOT stop for approval until the whole dev process is complete, except emergencies. Codified in `PROJECT_RULES.md`, `COUNCIL.md`, `CLAUDE.md`; memory `feedback_autonomous_execution`. Commit `48e0d7b`.
- **Delivered this run (autonomous, Council-gated, all pushed to `main`):**
  - **US-P0-06 i1** `cb25076` — zero-fiction static scan `app/core/fiction_policy.py` + ratchet test. Surfaced the beta synthetic ingest generators.
  - **US-P0-06 i2** `52dda91` — fixed a real fail-open leak: `_classify_source` is now an allowlist (`yfinance`/`chain` only); "local" beta data + unknown provenance fail closed. Full suite 1414.
  - **US-P0-06 i3** `ec6e944` — labeled seeded demo endpoints (`/regime`, `/scenario/*`) with `DEMO_DATA:` in `meta.warnings`. Full suite 1418.
- **State:** US-P0-06 substantially complete. All tests green; ruff/mypy clean each slice.
- **NEXT (continue autonomously, no approval needed):** **US-P0-07 freshness suppression audit**, then US-P0-04 (secure web session), then US-P0-05 (CSP). US-P0-03 remaining debt (192) is PARKED pending the beta auth-model product input — do not block other slices on it; pick a safe reversible default if it becomes necessary.

### Entry — 2026-07-21 · Resumed crashed P0/DecisionPacket task
- **User request:** Resume the multi-phase FINRLX P0 Truth & Safety + DecisionPacket implementation task (from the two Downloads ZIPs) that was interrupted by a crash; work per governance rules.
- **Key finding (truth-first):** The crashed session had **already delivered the entire DecisionPacket task (Phases A–F) on `main`** — commits `bb7b9cb`, `1772551`, `eb03555`, `c7fd0dd` (ADR-0001, DELTA+STATUS docs, `decision_packet.py`, `decision_truth.py`, feature-flagged `decision_packet_adapter.py` + API behind `decision_packet_v1`=OFF, P1 tests). Plus US-P0-01/03(i0,i1)/08. All pushed; origin==local.
- **What was in flight at crash:** US-P0-03 **increment 2** — auth-gating market-data ingestion. Completed this session.
- **What I did this session:**
  - Phase A baseline: confirmed repo root, ZIPs live OUTSIDE repo (`~/Downloads/finrl/`), Py3.11.9/Node24, baseline commit `5767a5c` in history, `main` in sync.
  - Verified + shipped the ingest-authz slice → commit **`28b8bf6`** on `main`.
  - Ran: 39 focused PASS, full backend suite **1394 passed / 2 skipped**, ruff clean, mypy(app/core) clean.
  - Excluded `research/finrlx_cpu/*.json` (test-run churn) from the commit — still dirty in tree by design.
- **State:** Increment 2 shipped & documented (DELTA + STATUS Slice 6). Council G4 logged.
- **Next action for a fresh session:** Pick the next P0 slice — see "Remaining P0 work" in `PROGRESS.md`. Top candidate: **US-P0-06 zero-fiction static scan**. US-P0-03 remaining debt (192) is blocked on a beta auth-model product decision (does the FE send a bearer on every call?) — ask user.

### Entry — 2026-07-21 · Governance infrastructure bootstrap
- **User request:** Build the universal project-rules file + crash-recovery memory file + agent-team + council + workflow + progress-table infrastructure (10 rules), show the structure, then continue development.
- **What was done:**
  - Created `/CLAUDE.md` (session bootstrap that forces reading the rules first).
  - Created `DOCS/governance/`: `PROJECT_RULES.md`, `SESSION_STATE.md` (this file), `AGENT_TEAM.md`, `COUNCIL.md`, `WORKFLOW.md`, `PROGRESS.md`, `README.md`.
- **State:** Governance layer authored, committed (`79f5621`), and pushed to `main`. Structure presented to user. Awaiting user's choice of next development track.
- **Next action for a fresh session:** Ask the user which track to resume (see "Open threads" below). Do NOT auto-commit the inherited P0 working-tree changes without user review.

---

## Current development context (inherited, pre-governance)

Source of truth before this file existed: root `RESUME.md` + git log. Summary:
- **Program LEAP** Plan v4.0 + Track B "Operation One Desk". F0–S9, A1–A6, K1(1–3) COMPLETE on `main`.
- **Desk W1 build** COMPLETE for structural scope (behind `FEATURE_DESK_V2`, flag OFF).
- Recent `main` commits center on **P0 security/ops user stories**: US-P0-01 (runtime inventory manifest), US-P0-03 (route authorization + governance-mutation auth), US-P0-08 (readiness endpoint + jobs component).
- **Uncommitted at governance-setup time** (do not lose): modifications to `ingest.py`, `route_policy.py`, several tests, registries; new file `backend/tests/test_p0_ingest_authz.py`.

## Open threads / next candidate work
- P0 track continuation (US-P0-xx security/ops hardening) — has uncommitted changes in the working tree.
- Browser phase per `DOCS/handoff/CLAUDE_CODE_HANDOFF_DESK_W1.md` (e2e matrix, screenshots, exit gates G-1..G-7, then flip `FEATURE_DESK_V2`).
- Operator items: E1 (rotate PAT — treat as compromised), E7 (torch worker), E8 (Finnhub social tier).

## Known caveats to carry forward
- 🟡 The working tree had **uncommitted P0 changes** when the governance layer was added. These are unrelated to governance and must be reviewed/committed separately with the user.
- 🟡 A stray Hebrew-named `.docx` at repo root ("טבלת שלבי הפיתוח...") is the legacy dev-stages table; `PROGRESS.md` supersedes it as the live table.

---

## How to update this file (checklist)
1. Prepend a new dated entry under **RESUME HERE** (most recent first).
2. State: request → actions taken → current state → explicit next action.
3. Move anything still pending into **Open threads**.
4. Record new caveats. Keep the file readable — trim entries older than the current milestone into a short rollup.
