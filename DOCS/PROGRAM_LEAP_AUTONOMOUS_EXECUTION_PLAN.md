# PROGRAM LEAP — Autonomous Step-Change Execution Plan for FINRLX

**Version:** 2.0 · **Date:** 2026-07-06 · **Supersedes:** v1.0 (same day)
**Companion:** `DOCS/handoff/FINRLX_DEEP_ANALYSIS_REPORT_2026-07-06.md` — every priority here traces to that report's evidence.

**Changelog:** v2.0 — added Autonomy Architecture (§2), expanded Decision Register to D1–D28 (§4), dependency graph + session budgets (§5), file-level task breakdowns, contracts, test plans and evidence lists per phase (§6), optional Hardening Track M1–M4 (§7), measurable program-exit KPIs (§8), expanded risk register (§9), appendices A–E (§10). v1.0 — initial program.

---

## 1. Purpose and operating contract

A complete, self-sufficient program for a significant step-change in FINRLX, written so an AI agent (Claude Code) executes **every phase end-to-end with zero decisions escalated to the operator**. All decisions are pre-made (§4), all gates are machine-verifiable (§6 + Appendix C), all rollbacks are mechanical (§3.4).

**Honest autonomy boundary.** An AI session cannot self-schedule across days and cannot spend money or create external accounts. Autonomy therefore means: operator involvement = one-time enablement checklist (§3.1) + one fixed kickoff sentence per phase (§3.2). Nothing returns to the operator mid-phase; divergences follow the pre-written fallbacks and are logged as Deviations in the phase report.

**Binding execution rules (inherited from `DOCS/FINRLX_UX_UI_TRANSFORMATION_MASTER_PLAN.md` §0):** inspect before editing; use the existing design foundation; no unsupported finance claims; research-only RL language; no hidden mock truth; readable typography; decision-first UX; mobile is not a squeezed desktop; no broad rewrites without tests; every phase ends with evidence.

---

## 2. Autonomy architecture — how a session runs itself

### 2.1 The phase loop
Every phase executes the same seven-step loop; the loop itself is the contract, so the operator never needs to supervise it:

1. **ORIENT** — read this plan, `DOCS/STATE_OF_THE_PRODUCT.md`, and the latest phase report in `DOCS/handoff/`; determine the next incomplete phase (Appendix A defines the DONE marker). Verify preconditions listed for the phase; if a precondition fails, apply its listed fallback or write a Blocked Report (§3.4) — never ask.
2. **BASELINE** — run `scripts/ci_gate.sh` on the untouched branch point. If red on unchanged code, this is hard-stop S2 territory only if production is down; a red *test* baseline instead becomes the first task of the phase (fix-forward, log as deviation).
3. **BRANCH** — `leap/L<n>-<slug>` from latest `master`.
4. **IMPLEMENT** — follow the phase's task breakdown in order. Each task lists its file touchpoints; the agent re-verifies each touchpoint exists before editing (D26 reality-wins rule).
5. **VERIFY** — run the phase gates exactly as written in Appendix C, capturing raw output.
6. **REPORT** — write the phase report from the template in Appendix A, including Deviations and the updated `STATE_OF_THE_PRODUCT.md`, in the same PR.
7. **MERGE & SMOKE** — merge when all gates green; run `deploy_smoke.sh`; on failure, mechanical revert (§3.4).

### 2.2 Context management (session survivability)
Phases are sized ≤ ~3 hours of agent work. If a session approaches its limits mid-phase, the agent commits WIP to the phase branch with a `WIP:` prefix and appends a `RESUME.md` at repo root listing exact remaining tasks; the next kickoff detects `RESUME.md` and continues the same phase instead of starting a new one. `RESUME.md` is deleted in the phase's final commit.

### 2.3 Self-verification discipline
Nothing counts as done on the agent's say-so. Each task's acceptance is a command with expected output (Appendix C) or a committed artifact (screenshot, JSON, log). Claims in reports must link to evidence files. This mirrors — deliberately — the project's existing hotfix history, where wording that outran evidence had to be corrected (Phases 7C1/7F1/7F2/8F1/8G1).

### 2.4 Deviation protocol
Deviation = any divergence from a task, decision, or gate. Allowed deviations: those with a listed fallback, and minimal scope trims under D26. Every deviation gets a row in the report: *what / why / fallback applied / debt created (Y/N, tracked where)*. Two or more deviations that weaken a gate = the gate fails.

---

## 3. Operator interface

### 3.1 One-time enablement checklist (once, then never again)

| # | Item | Why | If skipped |
|---|---|---|---|
| E1 | Revoke the GitHub PAT pasted into chat on 2026-07-06; create a **fine-grained** PAT scoped to `rotemyoeli/FINRLX` (contents R/W, pull-requests R/W); store as `GITHUB_TOKEN` where Claude Code runs. | Old token is exposed and over-scoped. | Program halts at gate G0.2. |
| E2 | Confirm Railway auto-deploys `master` (current `railway.toml` supports it: backend healthcheck `/healthz`, frontend `/`). Set `FINRLX_BACKEND_URL` + `FINRLX_FRONTEND_URL` in the execution env. | Enables autonomous post-merge verification via `scripts/deploy_smoke.sh`. | Phases merge; production verification marked SKIPPED. |
| E3 | (Optional) `ANTHROPIC_API_KEY` in Railway backend env. | Unlocks L8 annotations. | L8 ships flag-OFF with the existing "configure provider" empty state. |
| E4 | (Optional) `FINNHUB_API_KEY` (free tier, 60 calls/min) if unset. | Third leg of the L1 price chain. | Chain runs yfinance→Stooq→cache. |
| E5 | Branch protection on `master`: require the L0 CI workflow. | Converts gates from convention to enforcement. | Gates run; enforcement is agent discipline only. |
| E6 | (Optional) PostHog project API key confirmed in frontend env (already integrated). | L9 funnel verification against a real project. | Funnel verified in PostHog test mode only. |

### 3.2 Kickoff protocol — the operator's entire recurring job
Run in Claude Code at repo root, once per phase, in order:

```
Execute the next incomplete phase of DOCS/PROGRAM_LEAP_AUTONOMOUS_EXECUTION_PLAN.md.
Follow its Decision Register and gates exactly. Do not ask me anything.
```

### 3.3 What the operator receives per phase
One merged PR containing: code + tests, a phase report (Appendix A format) with raw gate output and screenshots, an updated `STATE_OF_THE_PRODUCT.md`, and — after merge — a smoke-test log line in the report addendum.

### 3.4 Mechanical failure handling
- **Post-merge smoke red →** `git revert <merge>`, push, re-smoke, incident note in report addendum. Never fix-forward on red production.
- **Blocked Report** (replaces the phase report when a hard stop fires): S1 credentials invalid; S2 production already down pre-phase; S3 gate requires money/external accounts; S4 change would weaken safe-language or research-isolation guarantees. The report states the stop, the evidence, and the single E-item or fix that unblocks it.

---

## 4. Decision Register — every decision pre-made (D1–D28)

The agent MUST NOT ask the operator; it applies the decision or its fallback and logs which path was taken.

**Data & pipeline**

| ID | Decision | Default | Fallback |
|---|---|---|---|
| D1 | Price provider chain order | `yfinance → stooq (keyless) → last-good cache (stale=true)` | Stooq unreachable in CI → chain ships yfinance→cache with the Stooq slot pluggable + tested via mock. |
| D2 | Fundamentals provider | Keep Finnhub pattern (Phase 16) untouched | — |
| D3 | Trading calendar | `exchange_calendars` PyPI; exchanges: XNYS primary, XTAE registered for future use | Dependency conflict → vendor minimal weekday+holiday table in `backend/app/utils/trading_calendar.py` covering 2020–2030. |
| D4 | Indicators | In-house pandas in `features.py`: MACD(12,26,9), RSI(14, Wilder), realized-vol 20/60d, turbulence index per FinRL-Meta definition; **no TA-Lib ever** (binary build risk on Railway) | — |
| D5 | Regime overlay | 26-week trend filter on universe benchmark + risk-off trigger when `drawdown_20d` breaches policy-config threshold for 3 consecutive sessions; outputs are labels + weight caps consumed by the pipeline — never autonomous trades; UI copy says "research overlay" | — |
| D6 | Price staleness thresholds | `fresh` ≤ 1 trading day behind expected latest bar; `stale` 2–5; `degraded` > 5 (uses L3 calendar; before L3, calendar-naive weekday logic with a `TODO(L3)` marker) | — |
| D7 | Provider provenance schema | Per stored bar: `{provider, fetched_at, request_window, chain_position}`; exposed on existing provenance surfaces | — |
| D8 | Data validation on ingest | Reject/flag bars failing: non-positive prices, >40% single-day move without split/dividend record, duplicate (ticker,date); flagged bars stored with `quality_flag`, excluded from features, surfaced in ops | — |

**Product & UX**

| ID | Decision | Default | Fallback |
|---|---|---|---|
| D9 | IA target | Exactly the 9-destination map in Appendix D; legacy paths 308-redirect forever via `next.config.js` `redirects()` seeded from `FINRLX_UX_PHASE_2_ROUTE_MIGRATION_MAP.csv` | A move breaking >5 e2e specs → keep old route as thin re-export, log debt row. |
| D10 | `/decision` layout | Two-pane ≥1024px (left: hero — headline, weight deltas, ConfidenceBlock trio, action row; right: dismissible evidence pane — stages, disagreement, audit drawer, publication-gate checklist); <1024px panes stack with evidence behind progressive disclosure | ContextPane unsuitable → new `DecisionEvidencePane`, do not touch ContextPane's other consumers. |
| D11 | Deep links | `/decision/[id]` against existing `/recommendations/{id}`; unknown id → PageEmpty with link to current; logged-out → login wall preserving return URL | — |
| D12 | Publication-gate checklist source | Render gates exactly as `publication.py` evaluates them; no frontend-invented gates | — |
| D13 | Tabs implementation (L5) | URL-addressable tabs (`/research?tab=analyze` or nested routes — whichever the existing router pattern in `/universe` uses; inspect first) so every tab is linkable | — |
| D14 | New UI vocabulary | Zero new colors/tokens; new components must pass local axe before merge; typography per Master Plan rule 6 | — |
| D15 | Empty/error/loading states | Reuse `PageLoading` / `PageError` / `PageEmpty` triad everywhere; no bespoke spinners | — |

**AI & research**

| ID | Decision | Default | Fallback |
|---|---|---|---|
| D16 | LLM annotations | Anthropic provider (existing `services/llm`), model `claude-sonnet-4-6`, ≤2 sentences, output contract in Appendix E.2 (must bind to source item id + freshness), flag `INSIGHTS_ANNOTATIONS` default OFF; auto-ON only after canary batch of 20 items passes contract validation | No key → flag stays OFF; UI uses existing "configure provider" empty state. |
| D17 | Shadow-RL artifact | One per program run: smallest-config PPO + A2C from `research/finrlx_cpu/sample_config.json`, imported via 8E validation, benchmarked via 8F vs. production heuristics, rendered in admin UI with existing isolation badges + sample-size caveats; wording passes the 7F/8F safe-language rules | CPU budget >10 min in CI → reduce timesteps to config minimum and label the limitation prominently. |
| D18 | RL promotion | Remains impossible; `not_eligible_for_promotion` invariant is regression-tested, not just labeled | — |
| D19 | Rename question | NOT in this program (irreversible brand decision = outside autonomy boundary); ship `/help` "relationship to FinRL-X" page instead, framing per analysis report | — |

**Engineering process**

| ID | Decision | Default | Fallback |
|---|---|---|---|
| D20 | Branching / commits / PRs | `leap/L<n>-<slug>`; Conventional Commits matching repo history (`feat(scope):`, `fix:`, `docs:`, `test:`); PR body = phase report summary + gate table (Appendix B) | — |
| D21 | Dependency policy | New Python: `exchange_calendars` only. New npm: none. | Anything else → in-house or drop sub-feature + debt row. |
| D22 | Test floor | Never reduce: backend pytest file count (94), frontend vitest count, e2e route coverage; new behavior ⇒ new tests | — |
| D23 | Feature flags | Backend env-var flags following the existing `FUNDAMENTALS_PROVIDER` pattern; names `LEAP_*` or feature-specific (`INSIGHTS_ANNOTATIONS`); every flag documented in `STATE_OF_THE_PRODUCT.md` | — |
| D24 | Migrations | Alembic, additive-only in this program (new tables/columns; no drops/renames); every migration has a downgrade | A required rename → additive new column + backfill + debt row for cleanup. |
| D25 | Telemetry | PostHog events namespaced `leap.*` (e.g. `leap.decision_deeplink_viewed`, `leap.evidence_expanded`); no PII in properties | — |
| D26 | Plan vs. reality conflict | Reality wins; re-verify, minimally adjust scope, log deviation | — |
| D27 | Performance budget (from M1; advisory before then) | Route JS ≤ 300KB gzipped; LCP ≤ 2.5s on `desktop-1280` local Lighthouse | Breach → log, don't block, until M1 makes it a gate. |
| D28 | Language/RTL | Program ships English-only; RTL groundwork is optional M2, never blocks core phases | — |

---

## 5. Program map

### 5.1 Dependency graph
```
L0 ──► L1 ──► L3 ──► L4 ──► L7
 │      │
 │      └───► L2
 ├────► L5 ──► L6
 ├────► L8   (needs L5's /insights rename; E3 optional)
 └────► L9 ──► L10  (L10 requires all merged phases)
Optional: M1..M4 after L10, any order.
```
Sequencing rule: numeric order L0→L10 satisfies the graph; the agent follows numeric order unless a phase is Blocked, in which case it may execute the next phase whose dependencies are met, logging the reorder.

### 5.2 Session budget

| Phase | Theme | Est. agent hours | Risk of overrun |
|---|---|---|---|
| L0 | Guardrails + truth baseline | 2–3 | Low |
| L1 | Price provider chain | 3 | Med (external endpoints) |
| L2 | A11y verified closure | 2 | Low |
| L3 | Trading calendar | 2 | Low |
| L4 | Features + regime overlay | 3 | Med (determinism gate) |
| L5 | IA consolidation | 3 | Med (blast radius) |
| L6 | Decision workspace | 3 | Med |
| L7 | Shadow-RL artifact | 2–3 | Med (CPU budget) |
| L8 | Sourced insights | 2 | Low |
| L9 | Truth surfaces + funnel | 2 | Low |
| L10 | Regression + close | 2 | Low |
| **Total core** | | **~26–28h ≈ 11 sessions** | |

---

## 6. Phases — full specifications

Common to all phases: Universal Gates U1–U7 (Appendix C.1) apply in addition to the listed phase gates; every phase updates `STATE_OF_THE_PRODUCT.md`; out-of-scope guard: touch nothing not listed in the task table except test files and docs.

---

### L0 — Bootstrap, guardrails, and truth baseline
**Rationale:** the program's gates must exist before anything else, and the site-wide contrast fix must move from "probably fixed" to *proven* (analysis §5.2).
**Preconditions:** E1 done (push access).

| # | Task | Touchpoints | Acceptance |
|---|---|---|---|
| 0.1 | `scripts/ci_gate.sh`: backend pytest → frontend `tsc --noEmit` + eslint + vitest → `next build` | new file | Exit 0 on unchanged repo; runtime logged |
| 0.2 | GitHub Actions workflow running 0.1 on PR + push to `leap/*` | `.github/workflows/leap-ci.yml` (new) | Green run visible on the PR |
| 0.3 | Re-run 25×4 production sweep; commit delta vs. `_phase18sweep_2026-05-23` baseline | `frontend/tests/e2e/_site-sweep.spec.ts`, evidence dir | Delta report: per-route axe counts, contrast status resolved to VERIFIED-FIXED or an exact violation list handed to L2 |
| 0.4 | Git-history secrets scan (regex classes: PATs, AWS, generic 32+ hex/base64 assignments) | `scripts/secrets_scan.sh` (new) | Zero live findings, or findings documented + rotation noted |
| 0.5 | `DOCS/STATE_OF_THE_PRODUCT.md` v1: shipped / flagged / stubbed / deferred feature index generated by cross-reading `FINRLX_UNIMPLEMENTED_FUNCTIONALITY_AUDIT.md` + code markers | new file | Every audit row H/M severity appears with a status + link |
| 0.6 | `RESUME.md` mechanism documented in CONTRIBUTING-style note | `DOCS/handoff/` | — |

**Gates:** G0.1 CI green on unchanged code · G0.2 push via fine-grained token confirmed (`git push` dry-run) · G0.3 sweep evidence committed · G0.4 secrets scan clean/documented.
**Evidence:** CI logs, sweep JSON + screenshots, scan output, state doc.
**Rollback:** trivial (additive files only).

---

### L1 — Price-data provider chain
**Rationale:** production ingestion rests on yfinance, documented ecosystem-wide as unfit for production (analysis §4); FINRLX already proved the chain pattern for fundamentals (Phase 17.4) and freshness watchdogs for FX.
**Preconditions:** L0.

| # | Task | Touchpoints | Acceptance |
|---|---|---|---|
| 1.1 | `stooq_provider.py` implementing the provider interface (inspect `yfinance_provider.py` + `validation.py` for the contract) | `backend/app/services/data_providers/` | Unit tests: happy path (recorded fixture), empty response, malformed CSV |
| 1.2 | Chain resolver in `ingest.py` mirroring the Phase 17.4 fundamentals chain; order per D1 | `backend/app/services/ingest.py` | Forced-failure tests: provider1 down → provider2 serves; both down → cache serves with `stale=true` |
| 1.3 | Provenance per bar per D7 (additive migration per D24) | models + `migrations/` | Migration up/down clean; provenance visible via existing provenance surfaces |
| 1.4 | Ingest validation per D8 (`quality_flag`) | `ingest.py`, ops surface | Adversarial fixtures rejected/flagged; flagged bars excluded from `features.py` |
| 1.5 | Equity price freshness watchdog generalizing `fx_freshness.py`; thresholds per D6 | `backend/app/services/` | Watchdog unit tests across fresh/stale/degraded |
| 1.6 | UI staleness surfacing on `/research/<ticker>`, `/decision`, `/analyze` via existing freshness components | frontend components | e2e: badge renders in each state (mocked API) |

**Gates:** G1.1 chain fallback tests green · G1.2 provenance recorded (DB assertion test) · G1.3 staleness badge e2e · G1.4 CI · G1.5 post-merge smoke.
**Rollback:** revert merge; migration downgrade verified pre-merge.

---

### L2 — Accessibility verified closure
**Rationale:** the only site-wide serious finding (contrast on all 25 routes) was token-patched but never re-proven; two serious items were explicitly deferred; authenticated flows have never been swept (project's own audit §3.3).
**Preconditions:** L0 (its sweep output is this phase's worklist).

| # | Task | Touchpoints | Acceptance |
|---|---|---|---|
| 2.1 | Fix any residual contrast violations from L0's delta | `frontend/src/app/globals.css` tokens first, per-component only if a token can't fix it | axe contrast = 0 on all routes |
| 2.2 | Recharts `<title>` accessibility on `/comparison` (5 nodes) | chart components | `svg-img-alt` = 0 |
| 2.3 | Underline inline links in MDX help renderer | help renderer styles | `link-in-text-block` = 0 |
| 2.4 | Short-circuit logged-out fetches on `/operator` `/paper` `/replay` behind `useAuth()` | 3 pages | Zero console 401s in sweep |
| 2.5 | First **authenticated** sweep using the Phase 19F template (seeded test user via `backend/seed.py` against local stack) | `frontend/tests/e2e/` | Authenticated report committed: per-route axe + console status for the 18 gated routes |

**Gates:** G2.1 logged-out sweep 0 critical + 0 serious across 25×4 · G2.2 authenticated sweep report committed (violations found become tracked debt rows, fix-now only if ≤30 min each) · G2.3 CI.

---

### L3 — Trading calendar
**Rationale:** calendar-naive date logic silently corrupts returns, freshness expectations, and rebalance timing (analysis §3 gap 3).
**Preconditions:** L1 (so the watchdog gains the calendar in one place).

| # | Task | Touchpoints | Acceptance |
|---|---|---|---|
| 3.1 | `trading_calendar.py` wrapping `exchange_calendars` per D3; API: `is_session(date)`, `sessions_in_range(a,b)`, `previous_session(date)`, `expected_latest_session(now)` | `backend/app/utils/` (new) | Property tests: weekends, US holidays incl. Good Friday/Thanksgiving, year boundary, DST boundary |
| 3.2 | Apply at ingestion date-range generation | `ingest.py` | No requests issued for non-sessions (assert in test) |
| 3.3 | Apply at freshness watchdogs (removes the `TODO(L3)` from L1) | watchdog services | Friday-close evaluated on Sunday = `fresh` |
| 3.4 | Apply at backtest/replay period arithmetic | `backtesting.py`, `replay.py`, `backtest_hygiene.py` | Hygiene + determinism suites green |

**Gates:** G3.1 property tests green · G3.2 `test_mvp6_replay_determinism.py` results unchanged for trading-day ranges · G3.3 CI + smoke.

---

### L4 — Feature vocabulary + regime overlay
**Rationale:** highest-value upstream gaps (analysis §3 gaps 1–2) closed without touching the DRL question; improves every existing engine and `/analyze` credibility.
**Preconditions:** L1 (clean data), L3 (calendar-correct windows).

| # | Task | Touchpoints | Acceptance |
|---|---|---|---|
| 4.1 | Indicators per D4 with per-feature provenance | `features.py` | Golden-value tests vs. hand-computed fixtures (fixture CSV committed) |
| 4.2 | Engine-config versioning so pre-L4 replays reproduce byte-identically | `engines.py`, `pipeline.py`, config records | Replay of a pre-L4 recommendation byte-identical (G4.2) |
| 4.3 | Regime overlay per D5 as a pipeline stage | `pipeline.py` + new `regime.py` service | Unit tests across trending/drawdown/sideways fixtures; caps applied to weights, visible in provenance |
| 4.4 | Render overlay state in existing `RiskOverlayStage` on `/decision`; research-only labeling per Master Plan rule 4 | `frontend/src/components/decision/RiskOverlayStage.tsx` | e2e renders all three regime states (mocked) |
| 4.5 | `/help` page: "What the regime overlay is and is not" | help content | Linked from the stage via existing `HelpLink` |

**Gates:** G4.1 golden tests · G4.2 byte-identical historical replay · G4.3 labeled UI e2e · G4.4 CI + smoke.
**Rollback note:** overlay ships behind `LEAP_REGIME_OVERLAY` flag (D23), default ON only after G4.2 passes; revert = flag OFF, no schema rollback needed.

---

### L5 — Information-architecture consolidation
**Rationale:** the master plan's stated core problem ("overloaded, non-intuitive") cannot resolve with ~25 top-level routes; the IA spec, migration CSV, and redirects mechanism already exist unexecuted (analysis §5.2). This is the UX step-change.
**Preconditions:** L0. **Target:** Appendix D route map (9 destinations).

| # | Task | Touchpoints | Acceptance |
|---|---|---|---|
| 5.1 | Inspect the tab/router pattern used by existing multi-view pages; fix tab mechanics per D13 | read-only recon | Decision logged in report |
| 5.2 | `/research` absorbs Analyze/Comparison/Backtests as URL-addressable tabs (old pages become tab content, not rewrites) | `frontend/src/app/research/`, moved modules | Each tab linkable; content pixel-equivalent (screenshot diff) |
| 5.3 | `/portfolio` parent with Paper/Risk/Replay tabs | new route + moved modules | Same standard |
| 5.4 | `/news` → `/insights` rename | route move | Old URL 308s |
| 5.5 | `/ops` absorbs Policies/Integrations/Templates/Operator as tabs | route moves | Same standard |
| 5.6 | `redirects()` block seeded from `FINRLX_UX_PHASE_2_ROUTE_MIGRATION_MAP.csv` + rows for 5.2–5.5 | `next.config.js` | e2e spec iterates every CSV row asserting 308→target |
| 5.7 | Nav (sidebar/TopBar) reduced to the 9 destinations; help docs + internal links updated (grep-driven) | nav components, MDX | Link-crawler spec: zero broken internal links |
| 5.8 | Update sweep spec to the new route list (keep legacy URLs in a redirect-assert list) | `_site-sweep.spec.ts` | Sweep green on new IA |

**Gates:** G5.1 all legacy URLs 308 (CSV-driven e2e) · G5.2 new-IA sweep 0 critical/serious axe, 0 console errors · G5.3 zero broken internal links · G5.4 CI · G5.5 smoke.
**Rollback:** revert merge restores old routes wholesale (moves are re-export-first per D9 fallback, so partial rollback is also clean).

---

### L6 — Decision workspace rebuild
**Rationale:** the product's core surface is "a long single scroll" with four backend-supported capabilities unrendered (audit rows 3–6); this is where the master plan's five questions must be answerable in seconds.
**Preconditions:** L5 (stable IA), L4 (overlay stage exists to slot into evidence).

| # | Task | Touchpoints | Acceptance |
|---|---|---|---|
| 6.1 | Two-pane layout per D10 | `frontend/src/app/decision/page.tsx` + new layout components | Screenshots at 1920/1280/mobile committed; mobile stacking per Master Plan rule 8 |
| 6.2 | `/decision/[id]` per D11 wired to `/recommendations/list` + `/recommendations/{id}` | new route, `services/api.ts` | e2e: deep link renders that exact recommendation; unknown id → PageEmpty; logged-out → login wall with return URL |
| 6.3 | Audit-trail drawer per recommendation | evidence pane + existing audit endpoint | Drawer shows provenance chain (fixture-driven test) |
| 6.4 | Publication-gate checklist per D12 | evidence pane, `publication.py` serializer | Checklist mirrors backend gate evaluation exactly (fixture matrix: all-pass, partial, all-fail) |
| 6.5 | Action row (save thesis / promote paper / defer) preserved with identical semantics | existing action handlers | Existing action tests green untouched |
| 6.6 | Telemetry per D25: `leap.decision_deeplink_viewed`, `leap.evidence_expanded`, `leap.gate_checklist_viewed` | analytics lib | Events assert-fired in e2e (test mode) |
| 6.7 | Flip audit rows 3–6 to DONE with evidence links | audit doc + state doc | — |

**Gates:** G6.1 deep-link e2e · G6.2 gate checklist fixture matrix · G6.3 mobile sweep clean on iPhone/Pixel viewports · G6.4 audit rows updated · G6.5 CI + smoke.

---

### L7 — Productive shadow-RL benchmark artifact
**Rationale:** convert the substantial RL investment (Phases 7–8) into a visible, truthful differentiator ("we test learning agents in the open and show the evidence") instead of parity anxiety — the stance the external literature supports (analysis §4).
**Preconditions:** L4 (features enrich the exported dataset), L0.

| # | Task | Touchpoints | Acceptance |
|---|---|---|---|
| 7.1 | Orchestrator `research/finrlx_cpu/scripts/run_leap_benchmark.(sh/ps1)`: export dataset (8I) → train PPO+A2C smallest config (D17) → export artifacts | research container | End-to-end run within CPU budget; artifacts conform to `artifact_schema.py` |
| 7.2 | Import via 8E validation path; benchmark via 8F vs. production heuristics | existing services | Import + benchmark tests green |
| 7.3 | Admin-UI "Research vs. Production — evidence report" page: equity curves, drawdowns, isolation badges, sample-size caveats, dataset fingerprint | admin frontend | Isolation badges + `not_eligible_for_promotion` on every candidate (G7.2) |
| 7.4 | Regression test: benchmark run has zero influence on `/recommendations/current` and publication workflow | backend tests | G7.3 |
| 7.5 | All copy passes safe-language rules (checklist from 7F/8F reports embedded in test as string assertions) | frontend + report copy | Wording test green |

**Gates:** G7.1 e2e run in budget · G7.2 isolation invariants rendered + regression-tested (D18) · G7.3 zero-influence test · G7.4 CI + smoke.

---

### L8 — Sourced "why this matters" insights
**Rationale:** first production LLM feature, chosen because it is the lowest-risk expression of the plan's own AlphaSense rule (source-grounded AI, never blank-chat) and reuses shipped plumbing.
**Preconditions:** L5 (`/insights` exists). E3 optional.

| # | Task | Touchpoints | Acceptance |
|---|---|---|---|
| 8.1 | Annotation job per D16 with output contract Appendix E.2 | `backend/app/services/llm/`, `news.py`, jobs | Contract validator rejects adversarial fixtures (missing source binding, >2 sentences, advice-like language) |
| 8.2 | Backend `?sentiment=&ticker=` filters (audit rows 11/13) | news API | Filter tests |
| 8.3 | Frontend chip + freshness stamp per item; flag-OFF renders today's experience untouched | `/insights` page | Both flag states e2e-tested |
| 8.4 | Canary: 20-item batch must pass validation before auto-ON | job logic | Canary logic unit-tested |

**Gates:** G8.1 contract validator adversarial tests · G8.2 flag-OFF regression · G8.3 CI + smoke (flag state per E3).

---

### L9 — Truth & positioning surfaces
**Rationale:** closes strategic-honesty items reversibly (D19) and instruments the north-star UX metric.

| # | Task | Touchpoints | Acceptance |
|---|---|---|---|
| 9.1 | `/help` "Relationship to FinRL-X" page: shared weight-centric architecture, deliberately different mission, no execution, research-only RL — framing from the analysis report | help MDX | Copy passes safe-language wording test |
| 9.2 | Refresh "What FINRLX is not" for post-LEAP reality | help MDX | — |
| 9.3 | State-of-product drift check: script cross-references audit/status rows vs. code markers; wired into CI | `scripts/state_drift_check.py`, CI | Deliberately-broken fixture fails CI |
| 9.4 | Time-to-first-insight funnel: `leap.signup_completed` → `leap.first_recommendation_viewed` → `leap.evidence_expanded`; dashboard-setup runbook | analytics + `DOCS/operator/` | Events fire in e2e (PostHog test mode; live verify if E6) |

**Gates:** G9.1 drift check enforced in CI · G9.2 funnel events asserted · G9.3 CI + smoke.

---

### L10 — Program close: regression + release report
| # | Task | Acceptance |
|---|---|---|
| 10.1 | Full unauthenticated + authenticated sweeps on final IA | 0 critical/serious axe; 0 console errors |
| 10.2 | Full CI + production smoke | Green |
| 10.3 | `DOCS/handoff/PROGRAM_LEAP_CLOSE_REPORT.md`: per-phase evidence index, deviations ledger, debt register, KPI table (§8) filled with measured values | Committed |
| 10.4 | Tag `leap-v1` on `master` | Tag pushed |

**Gates:** G10.1 all green · G10.2 close report + tag.

---

## 7. Optional Hardening Track (M1–M4) — run after L10, any order

| Phase | Objective | Core gates |
|---|---|---|
| **M1 Performance** | Lighthouse CI on the 9 destinations; enforce D27 budgets (route JS ≤300KB gz, LCP ≤2.5s); bundle-analysis report; convert D27 from advisory to blocking | Budgets pass or per-route waiver documented |
| **M2 RTL/Hebrew groundwork** | Logical CSS properties sweep (`ml-`→`ms-` etc.), `dir` plumbed through layout, one pilot page (`/help`) rendered RTL, i18n scaffolding for the existing `i18n/` dir — **no translation content** in this program | RTL pilot screenshot set; zero layout breakage LTR |
| **M3 Data-quality suite** | Cross-provider price validation (yfinance vs. Stooq sample disagreement report), corporate-action sanity checks, weekly anomaly report to ops surface | Disagreement report generated; anomalies surfaced with quality_flag pipeline from L1 |
| **M4 DR drill automation** | Script the existing `DR_RUNBOOK.md` into a rehearsable restore drill against a scratch database; timing report | Drill completes; RTO/RPO measured and recorded |

---

## 8. Program-exit KPIs — what "step-change achieved" means, measurably

| # | KPI | Baseline (evidence) | Exit target |
|---|---|---|---|
| K1 | Primary navigation destinations | ~25 routes (Phase 18J sweep list) | ≤ 9 |
| K2 | Serious+critical axe violations, all routes × 4 viewports | contrast on 25/25 routes at 2026-05-23; residual TBD at L0 | 0, proven twice (L2, L10) |
| K3 | Price-data single point of failure | 1 provider (yfinance) | 3-leg chain + visible staleness states |
| K4 | Decision page: master-plan questions answerable without scrolling past fold (desktop) | No (single scroll; audit rows 3–6 open) | Yes: deltas, confidence trio, action, gates visible; evidence one click |
| K5 | `/decision/[id]` shareable deep links | Absent | Present + e2e-tested |
| K6 | Calendar-aware date logic | Absent | Present at 3 call-site families |
| K7 | Feature vocabulary | 6 features, no MACD/RSI/turbulence | +4 indicator families, golden-tested, replay-safe |
| K8 | RL value visible to users | None (isolated research only) | 1 truthful benchmark evidence page with isolation invariants regression-tested |
| K9 | Authenticated a11y coverage | Never swept (audit §3.3) | Swept + violations triaged |
| K10 | Doc drift protection | None (180+ files, no index) | STATE_OF_THE_PRODUCT + CI drift check |
| K11 | Time-to-first-insight | Unmeasured | Instrumented funnel live |

---

## 9. Risk register (expanded)

| Risk | L | Impact | Mitigation | Residual |
|---|---|---|---|---|
| Yahoo/Stooq endpoint changes mid-program | M | L1 flaky | Recorded fixtures for unit tests; live calls only in optional integration job; chain is the mitigation | Low |
| IA move breaks bookmarks/e2e en masse | M | L5 overrun | CSV-driven 308s; re-export-first moves; D9 fallback | Low |
| Config-versioning miss breaks replay determinism | L | Trust damage | G4.2 byte-identical gate blocks merge; flag rollback path | Low |
| Agent context exhaustion on L5/L6 | M | Half-done phase | §2.2 RESUME.md protocol | Low |
| Railway deploy drift vs. local | L | Prod incident | Smoke after every merge; mechanical revert | Low |
| CPU RL run exceeds budget | M | L7 thin results | D17 fallback + labeled sample-size caveats | Med (accepted: honesty over impressiveness) |
| LLM annotation contract drift / hallucinated claims | M | Trust damage | Appendix E.2 contract + adversarial validator + canary + flag | Low |
| Alembic migration failure on prod deploy | L | Outage | Additive-only (D24), downgrade tested pre-merge, healthcheck blocks routing until `alembic upgrade head` succeeds (existing railway.toml behavior) | Low |
| Documentation drift recurring | H | Compounding confusion | Per-PR state-doc updates from L0; CI drift check from L9 | Low after L9 |
| Scope creep via "while I'm here" edits | M | Review burden, regressions | Out-of-scope guard per phase; deviations ledger makes creep visible | Low |

---

## 10. Appendices

### A. Phase report template (house format, extended)
```
# PHASE L<n> — <name> REPORT
Date / Branch / PR / Base commit
1. Objective (one paragraph, traces to plan §6)
2. Work performed (task table with DONE/PARTIAL/DROPPED + evidence links)
3. Gate results (raw command output blocks, pass/fail table)
4. Evidence index (screenshots, JSON, logs — committed paths)
5. Deviations (what / why / fallback / debt Y-N)
6. Known gaps & debt rows created
7. STATE_OF_THE_PRODUCT delta summary
8. Next step (which phase unblocks)
Addendum (post-merge): smoke output; incident note if any.
DONE marker: the merged PR + this report's presence in DOCS/handoff/ = phase complete.
```

### B. Commit & PR conventions
Conventional Commits with scopes matching repo history (`feat(universe-ui):`, `fix(analysis):` …). PR title = `LEAP L<n>: <name>`. PR body = report sections 1–3. One PR per phase; stacked PRs forbidden (keeps rollback mechanical).

### C. Gate command reference
**C.1 Universal gates (every phase):**
- U1 `bash scripts/ci_gate.sh` → exit 0
- U2 `npx playwright test <touched-surface specs>` → green; axe on touched routes: 0 critical/serious
- U3 test floor: `find backend/tests -name 'test_*.py' | wc -l` ≥ 94; vitest suite count ≥ baseline recorded in L0 report
- U4 `git diff master --stat` contains no dependency-manifest changes beyond D21
- U5 report per Appendix A committed in the PR
- U6 `DOCS/STATE_OF_THE_PRODUCT.md` updated in the PR
- U7 post-merge `FINRLX_BACKEND_URL=… FINRLX_FRONTEND_URL=… bash scripts/deploy_smoke.sh` → exit 0 (or SKIPPED per E2)

**C.2 Selected phase-gate commands:** sweep `npx playwright test frontend/tests/e2e/_site-sweep.spec.ts`; determinism `pytest backend/tests/test_mvp6_replay_determinism.py -q`; redirects `npx playwright test frontend/tests/e2e/leap-redirects.spec.ts` (new, CSV-driven); drift `python scripts/state_drift_check.py`.

### D. Final IA route map (9 destinations)
| Destination | Absorbs | Legacy 308s |
|---|---|---|
| `/` Home | — | — |
| `/decision`, `/decision/[id]` | — | — |
| `/research` (tabs: Ticker · Analyze · Comparison · Backtests) | `/analyze`, `/comparison`, `/backtests` | those 3 |
| `/portfolio` (tabs: Paper · Risk · Replay) | `/paper`, `/risk`, `/replay` | those 3 |
| `/insights` | `/news` | `/news` |
| `/universe` | — | — |
| `/help` | — | — |
| `/ops` (tabs: Overview · Policies · Integrations · Templates · Operator) | `/policies`, `/integrations`, `/templates`, `/operator` | those 4 |
| `/admin` | — | — |
Auth/legal (`/login`, `/signup`, `/onboarding`, `/profile`, `/feedback`, `/disclaimer`, `/privacy`, `/terms`) unchanged; `/profile` and `/feedback` reachable from the avatar menu, not primary nav.

### E. Data contracts
**E.1 Price bar provenance (D7):** `{provider: "yfinance"|"stooq"|"cache", fetched_at: ISO8601, request_window: {start,end}, chain_position: 1|2|3, quality_flag: null|"suspect_move"|"duplicate"|"nonpositive"}` — additive columns, exposed through existing provenance serializers.
**E.2 Insight annotation contract (D16):** `{item_id, annotation: string(≤2 sentences), source_binding: {item_id, published_at}, model, generated_at, freshness_stamp}` — validator rejects: missing/mismatched `source_binding`, sentence count >2, imperative/advice verbs list ("buy", "sell", "should", "guaranteed" …), any ticker not present in the source item.
**E.3 Benchmark artifact (D17):** conforms to existing `research/finrlx_cpu/artifact_schema.py` plus `{dataset_fingerprint, timesteps, seed, isolation: {research_only, offline_only, shadow_only, not_eligible_for_promotion, no_broker_execution, no_publication_influence}: all true}` — the isolation object is asserted `true` by the L7 regression test, not merely displayed.

---

*End of plan v2.0. This document is the single source of truth for Program LEAP; amendments are committed as v2.x with a changelog line.*
