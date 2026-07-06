# PROGRAM LEAP — Autonomous Step-Change Execution Plan for FINRLX

**Version:** 1.0 · **Date:** 2026-07-06 · **Author:** Claude (analysis session, HEAD `4d5ce7d`)
**Companion document:** `FINRLX_Deep_Analysis_Report_2026-07-06.md` (external analysis; all priorities here trace to its P0/P1/P2 findings)

---

## 1. Purpose and operating contract

This is a complete, self-sufficient work program for a significant step-change in FINRLX. It is written so that an AI agent (Claude Code) can execute **every phase end-to-end with zero decisions escalated to the operator**. All product, technical, and design decisions are pre-made in the Decision Register (§3). All quality gates are machine-verifiable (§5). All rollbacks are mechanical (§6).

**Honest autonomy boundary.** An AI session cannot self-schedule across days. Autonomy here means: the operator's total involvement is (a) a one-time enablement checklist (§2, ~15 minutes, done once), and (b) launching each phase with the single fixed kickoff command in §7. Nothing else. No questions will come back mid-phase; where reality diverges from the plan, the agent follows the pre-written fallback in the Decision Register, records the deviation in the phase report, and continues.

**Execution style contract (inherited from the UX Master Plan §0, binding):** inspect before editing; no unsupported finance claims; research-only RL language; no hidden mock truth; every phase ends with a report + test logs + evidence in `DOCS/handoff/` following the existing house format; work on a branch, never directly on `master`.

---

## 2. One-time enablement checklist (operator, once, then never again)

| # | Item | Why | If skipped |
|---|---|---|---|
| E1 | Revoke the GitHub PAT that was pasted into chat on 2026-07-06; create a **fine-grained** PAT scoped to `rotemyoeli/FINRLX` only (contents: read/write, pull requests: read/write) and store it where the executing agent runs (Claude Code keychain / env `GITHUB_TOKEN`). | The old token is exposed and over-scoped. | Program halts at Phase L0 gate G0.2. |
| E2 | Confirm Railway auto-deploys `master` for both services (current `railway.toml` files support it). Set env `FINRLX_BACKEND_URL` and `FINRLX_FRONTEND_URL` in the execution environment for smoke tests. | Enables autonomous verify-after-merge via `scripts/deploy_smoke.sh`. | Phases still merge; production verification is marked SKIPPED in reports. |
| E3 | (Optional) Set `ANTHROPIC_API_KEY` in Railway backend env. | Unlocks Phase L8 ("why this matters" annotations). | L8 ships feature-flagged OFF with graceful empty state; program continues. |
| E4 | (Optional) Set `FINNHUB_API_KEY` (free tier) if not already set. | Strengthens provider chain in L1. | L1 uses the keyless Stooq fallback only. |
| E5 | Create branch protection on `master`: require the CI script (added in L0) to pass. | Converts the plan's gates from convention to enforcement. | Gates still run, but enforcement is by agent discipline only. |

After E1–E5, the operator's only remaining action is issuing the kickoff command per phase (§7).

---

## 3. Decision Register — all decisions pre-made

Every fork in the road is decided here. The agent MUST NOT ask the operator; it applies the decision, or the listed fallback, and logs which path was taken.

| ID | Decision | Chosen default | Fallback if blocked |
|---|---|---|---|
| D1 | Price-data provider chain order | `yfinance → stooq (keyless) → last-good cache with staleness flag` | If Stooq unreachable in CI, ship chain with cache-only fallback; mark provider slot pluggable. |
| D2 | Fundamentals provider | Keep Finnhub pattern (Phase 16) untouched | — |
| D3 | Trading calendar library | `exchange_calendars` (PyPI, maintained) | If dependency conflict: vendor a minimal NYSE/TASE weekday+holiday table in `backend/app/utils/trading_calendar.py`. |
| D4 | Technical indicators source | Implement in-house in `features.py` (pandas, no TA-Lib binary dep): MACD(12,26,9), RSI(14), rolling vol regimes, turbulence index per FinRL-Meta definition | Never add TA-Lib (binary build risk on Railway). |
| D5 | Regime overlay rules | 26-week trend filter on universe benchmark + 3-day risk-off trigger on drawdown_20d > threshold from policy config; overlay outputs are *labels + weight caps*, never autonomous trades; all UI copy uses "research overlay" language | — |
| D6 | IA target | ≤ 9 primary destinations exactly as specified in §L5; implement via `next.config.js` `redirects()` + route moves; old URLs 308-redirect forever | If a route move breaks >5 e2e specs, keep old route mounted as thin re-export and log as debt. |
| D7 | `/decision` rebuild pattern | Two-pane: left decision hero (headline, deltas, ConfidenceBlock, action row), right dismissible ContextPane (stages, disagreement, audit drawer, publication gates); `/decision/[id]` deep links against existing `/recommendations/{id}` backend | If ContextPane component is unsuitable, build `DecisionEvidencePane` beside it; do not modify ContextPane's other consumers. |
| D8 | Shadow-RL artifact cadence | One benchmark comparison artifact per program run (not calendar-monthly — agent can't self-schedule); generated by extending existing 8F–8K machinery; admin-UI page with existing isolation badges | If CPU training in CI exceeds 10 min, use the smallest timesteps config in `research/finrlx_cpu/sample_config.json` and label sample-size limits. |
| D9 | LLM annotations | Anthropic provider (existing Phase 17 plumbing), `claude-sonnet-4-6`, max 2-sentence "why this matters" per news item, mandatory source chip + freshness stamp, feature flag `INSIGHTS_ANNOTATIONS` default OFF until E3 key present | No key → flag stays OFF, UI shows the existing "configure provider" empty-state pattern. |
| D10 | Rename question | Do NOT rename in this program (irreversible brand decision = outside autonomy boundary). Instead ship `/help/relationship-to-finrl-x` page with truthful framing per analysis report §6 R8. | — |
| D11 | Design system | Reuse existing tokens/components exclusively; zero new colors; any new component must pass axe locally before merge | — |
| D12 | Test floor | No phase may reduce: backend pytest count (94 files), frontend vitest count, or e2e route coverage (25 routes) | — |
| D13 | Dependency policy | New Python deps allowed: `exchange_calendars` only. New npm deps: none. | Anything else → implement in-house or drop the sub-feature and log. |
| D14 | Conflict between this plan and repo reality | Reality wins; agent re-verifies the claim, adjusts scope minimally, logs deviation in phase report §"Deviations" | — |

---

## 4. Program structure — phases L0–L10

Each phase = one Claude Code session (target ≤ 3 hours agent time), one branch `leap/L<n>-<slug>`, one PR to `master`, gates green before merge, phase report committed with the PR.

### L0 — Bootstrap, guardrails, and truth baseline
**Objective:** make the program enforceable and establish a verified baseline.
**Work:** (1) add `scripts/ci_gate.sh` running: backend pytest, frontend vitest + tsc + eslint, Playwright build-sweep locally; (2) add GitHub Actions workflow calling it; (3) re-run the full 25×4 site sweep (`_site-sweep.spec.ts`) against production and commit the delta vs. the 2026-05-23 baseline — this converts the token contrast fix from "probably fixed" to *verified* or produces the exact remaining violation list for L2; (4) secrets scan of full git history (`gitleaks`-style regex pass); (5) create `DOCS/STATE_OF_THE_PRODUCT.md` v1 auto-generated from the Unimplemented Functionality Audit + shipped-features scan — the living document all later phases must update.
**Gates:** G0.1 CI green on unchanged code; G0.2 push access via fine-grained token confirmed; G0.3 sweep evidence committed; G0.4 zero live secrets in history (or documented + rotated).

### L1 — Price-data provider chain (P0, highest risk reduction)
**Objective:** remove the single-point-of-failure on yfinance documented in the analysis report §4.
**Work:** add `stooq_provider.py` beside `yfinance_provider.py`; chain resolution in `ingest.py` mirroring Phase 17.4's fundamentals-chain pattern; per-provider provenance on every stored bar; cache-serving with `stale=true` flag when both live providers fail; extend the FX freshness-watchdog pattern (`fx_freshness.py`) to equity prices; surface staleness through the existing freshness UI components on `/research`, `/decision`, `/analyze`.
**Gates:** G1.1 unit tests for chain fallback order incl. forced-failure of provider 1 and 1+2; G1.2 provenance recorded per bar; G1.3 UI staleness badge e2e test; G1.4 full CI green; G1.5 post-merge `deploy_smoke.sh` pass (or SKIPPED if E2 absent).

### L2 — Accessibility verified closure (P0)
**Objective:** zero serious/critical axe violations on all 25 routes, proven.
**Work:** fix whatever L0's sweep still shows for `color-contrast`; add Recharts `<title>` wrappers on `/comparison` charts; underline inline links in the MDX help renderer; short-circuit the three logged-out 401 fetches (`/operator`, `/paper`, `/replay`) behind `useAuth()`; run one **authenticated** sweep using the Phase 19F template (first time ever, per the project's own audit).
**Gates:** G2.1 axe: 0 critical + 0 serious across 25×4 logged-out; G2.2 authenticated sweep report committed; G2.3 CI green.

### L3 — Trading calendar (P0)
**Objective:** eliminate the silent-correctness bug class in returns/freshness/rebalance timing.
**Work:** `backend/app/utils/trading_calendar.py` wrapping `exchange_calendars` (per D3), applied at the three call-site families: ingestion date-range generation, freshness watchdog "expected latest bar" logic, and backtest/replay period arithmetic. Property tests: weekends, US holidays, year boundaries.
**Gates:** G3.1 all watchdog + backtest-hygiene tests green with calendar active; G3.2 replay determinism suite (`test_mvp6_replay_determinism.py`) unchanged results on trading days; G3.3 CI green.

### L4 — Feature vocabulary + regime overlay (P1, product value)
**Objective:** close the highest-value upstream gaps (analysis §3) without touching the DRL question.
**Work:** implement D4 indicators in `features.py` with per-feature provenance; add regime overlay per D5 as a new pipeline stage rendered in the existing `RiskOverlayStage` component; new features feed existing engines behind explicit engine-config versioning so historical replays remain reproducible (backtest-hygiene rule); `/help` doc "What the regime overlay is and is not."
**Gates:** G4.1 golden-value unit tests for each indicator vs. hand-computed fixtures; G4.2 replay of a pre-L4 recommendation still byte-identical (config versioning proof); G4.3 overlay visible on `/decision` with research-only labeling; G4.4 CI green.

### L5 — Information-architecture consolidation (P1, the UX step-change)
**Objective:** collapse ~25 top-level routes into ≤ 9 primary destinations, executing the project's own dormant Phase 2 IA spec.
**Target IA (final, per D6):** `/` Home · `/decision` (+`/decision/[id]`) · `/research` (tabs: Ticker, Analyze, Comparison, Backtests) · `/portfolio` (tabs: Paper, Risk, Replay) · `/insights` (was `/news`) · `/universe` · `/help` · `/ops` (tabs: Overview, Policies, Integrations, Templates, Operator) · `/admin`. Auth/legal routes unchanged.
**Work:** route moves as re-exports first, then `redirects()` block (308) for every legacy path from the existing `FINRLX_UX_PHASE_2_ROUTE_MIGRATION_MAP.csv`; sidebar/TopBar nav update; update the site-sweep spec route list; update help docs and internal links (grep-driven).
**Gates:** G5.1 every legacy URL 308-redirects to its new home (e2e spec asserting all rows of the migration CSV); G5.2 sweep on the NEW route list: 0 critical/serious axe, 0 console errors; G5.3 no broken internal links (crawler spec); G5.4 CI green; G5.5 post-merge smoke.

### L6 — Decision workspace rebuild (P1, core-surface step-change)
**Objective:** turn the product's most important page from a scroll into a workflow.
**Work:** implement D7 two-pane layout; `/decision/[id]` deep links against existing backend `/recommendations/{id}`; audit-trail drawer (backend endpoint exists per audit row 5); publication-gate checklist rendered per recommendation from `publication.py` gates (audit row 6); mobile: panes stack, evidence behind progressive disclosure (Master Plan rule 8).
**Gates:** G6.1 e2e: deep link renders the exact recommendation, shareable when logged in; G6.2 gate checklist reflects backend state (fixture-driven test); G6.3 mobile sweep on iPhone/Pixel viewports clean; G6.4 the four decision-page rows (3–6) in `FINRLX_UNIMPLEMENTED_FUNCTIONALITY_AUDIT.md` flipped to DONE with evidence links; G6.5 CI green.

### L7 — Productive shadow RL benchmark artifact (P1)
**Objective:** convert the RL investment into a visible, truthful feature (analysis §6 R4).
**Work:** orchestration script that (1) exports a dataset via the existing Phase 8I export, (2) trains smallest-config PPO + A2C in `research/finrlx_cpu` (D8), (3) imports artifacts through the 8E validation path, (4) runs the 8F benchmark vs. production heuristics, (5) renders an admin-UI "Research vs. Production — evidence report" page with the existing isolation badges and sample-size caveats. All wording passes the safe-language rules from the 7F/8F hotfix history.
**Gates:** G7.1 end-to-end run completes on CPU within budget; G7.2 report page shows isolation badges + `not_eligible_for_promotion` on every candidate; G7.3 zero influence on `/recommendations/current` (regression test); G7.4 CI green.

### L8 — Insights: "why this matters" with source chips (P1)
**Objective:** first production LLM feature under the AlphaSense-style governance rule already written into the Master Plan.
**Work:** per D9 — backend annotation job on news items via existing `services/llm` Anthropic provider; strict output contract (2 sentences, must cite source item); frontend chip + freshness stamp on `/insights`; feature flag default OFF, auto-ON when key present and a canary batch passes contract validation; add backend `?sentiment=&ticker=` filters (closes audit rows 11/13).
**Gates:** G8.1 contract validator rejects annotations without source binding (test with adversarial fixture); G8.2 flag-OFF path renders existing experience untouched; G8.3 CI green.

### L9 — Truth & positioning surfaces (P2)
**Objective:** close the strategic-honesty items without irreversible brand moves.
**Work:** `/help/relationship-to-finrl-x` page (D10) with the factual framing from the analysis report; refresh "What FINRLX is not"; finalize `STATE_OF_THE_PRODUCT.md` as auto-checked index (script cross-references audit rows vs. code markers, fails CI on drift); PostHog funnel definition for time-to-first-insight (signup → first recommendation viewed with evidence expanded) committed as code + dashboard-setup runbook.
**Gates:** G9.1 state-of-product drift check wired into CI; G9.2 funnel events firing in e2e (PostHog test mode); G9.3 CI green.

### L10 — Program close: full regression + release report
**Work:** full authenticated + unauthenticated sweep on final IA; complete CI; production smoke; write `DOCS/handoff/PROGRAM_LEAP_CLOSE_REPORT.md` — per-phase evidence links, deviations log, remaining-debt register, and the updated audit table.
**Gates:** G10.1 everything green; G10.2 close report committed; program ends.

---

## 5. Universal gate definition (applies to every phase)

A phase may merge only when ALL hold, verified by command output captured into the phase report:
1. `scripts/ci_gate.sh` exit 0 (pytest + vitest + tsc + eslint + build).
2. Playwright e2e relevant to touched surfaces: green; axe on touched routes: 0 critical, 0 serious.
3. Test floor (D12) not reduced; new behavior has new tests.
4. No new dependencies beyond D13.
5. Phase report in `DOCS/handoff/` using the existing house format (objective, work, evidence, test logs, screenshots, deviations, known gaps, next step).
6. `STATE_OF_THE_PRODUCT.md` updated in the same PR.
7. Post-merge: `deploy_smoke.sh` against production (or SKIPPED-with-reason if E2 not done).

## 6. Rollback and stop conditions (mechanical, no judgment calls)

- **Rollback:** any post-merge smoke failure → `git revert` the merge commit, push, re-run smoke, log incident in phase report. No forward-fixing on red production.
- **Hard stops (agent halts the phase and writes a blocked-report instead of asking questions):** (S1) credentials invalid/expired; (S2) production smoke failing *before* the phase begins (pre-existing outage); (S3) a gate requires spending money or creating external accounts; (S4) any change that would require weakening safe-language/isolation guarantees. Everything else has a fallback in §3 and does not stop.

## 7. Kickoff protocol (the operator's entire job)

Run in Claude Code at the repo root, once per phase, in order:

```
Execute the next incomplete phase of DOCS/PROGRAM_LEAP_AUTONOMOUS_EXECUTION_PLAN.md.
Follow its Decision Register and gates exactly. Do not ask me anything.
```

Phase completion state is self-evident from merged PRs + phase reports; the agent determines "next incomplete phase" from `STATE_OF_THE_PRODUCT.md` + `DOCS/handoff/` contents. Estimated program size: 11 sessions.

## 8. Risk register

| Risk | Likelihood | Mitigation in-plan |
|---|---|---|
| Upstream data endpoints change mid-program | Med | L1 chain + cache-first is itself the mitigation; D1 fallback |
| IA move breaks bookmarks/e2e en masse | Med | 308 redirects from existing migration CSV; D6 fallback keeps thin re-exports |
| Config-versioning miss breaks replay determinism | Low | G4.2 byte-identical replay gate blocks merge |
| Agent context limits on big phases (L5, L6) | Med | Phases scoped to ≤3h; D14 permits minimal scope trim with logged deviation |
| Railway deploy drift vs. local | Low | Smoke script after every merge; mechanical revert rule |
| Documentation drift (the project's chronic risk) | High | STATE_OF_THE_PRODUCT drift check in CI from L9; updates mandatory per-PR from L0 |

---

*End of plan. This document is the single source of truth for Program LEAP; any amendment must be committed as v1.x with a changelog line here.*

**Changelog:** v1.0 — initial program (2026-07-06).
