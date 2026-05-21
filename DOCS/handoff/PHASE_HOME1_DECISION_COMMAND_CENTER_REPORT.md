# Phase HOME-1 — FINRLX Decision Command Center

Date: 2026-05-21
Branch: `main`
Commit before changes: `f0d56ca`

## 1. Objective

Replace the previous greeting + three-tile overview at `/` with a serious,
trust-first, decision-oriented command center. Within 5 seconds of load, the
home page must answer:

1. **What changed?**
2. **What requires review?**
3. **What evidence supports each item?**
4. **What is safe, stale, shadow-only, or blocked?**

The page is **not** a market portal. It is a triage surface for an operator
that does not need a streaming chart, a generic news feed, or a "buy now"
CTA.

## 2. External product research

Patterns extracted from competitor screens (TradingView, Koyfin, Finviz,
TipRanks, TrendSpider, Simply Wall St) and Reddit pain-point threads —
references were studied but no copyrighted UI was reproduced.

Lessons that shaped FINRLX HOME-1:

- **Users hate friction before their primary task.** TradingView pre-roll
  complaints (Reddit r/TradingView "nobody gives a damn about 90% of your…")
  make the case for surfacing the operator's primary triage queue *above*
  marketing widgets. FINRLX puts the decision queue, opportunity radar, and
  governance status above the fold; everything else lives below.
- **Screening is not conviction.** r/ValueInvesting Finviz-alternative
  threads show screeners aren't enough for serious fundamental conviction.
  FINRLX's "Opportunity Radar" is explicitly framed as
  "Top-conviction picks from the current recommendation", not a market-wide
  scanner.
- **AI is useful as source-grounded assistance, not as an autonomous
  analyst.** r/investing and r/stocks threads on LLM stock-picking show
  users want screening, summarization, and risk-finding — not a black-box
  "AI pick". The Research Assistant card is a non-interactive preview with
  hard rules: source-grounded answers, no trade instructions.
- **No broker linking expected for trust.** r/investing portfolio-tracking
  threads show users specifically prefer paper-tracking flows over broker
  OAuth. FINRLX's home explicitly states "No broker execution" and links
  to the paper portfolio, never to a brokerage flow.
- **NN/g preattentive dashboard guidance** (nngroup.com) — color is reserved
  for semantic status: warning, breach, OK, unavailable. No decorative
  color, no information-dense charts above the fold.

## 3. Files changed

| File | Change | Purpose |
|---|---|---|
| `frontend/src/app/page.tsx` | rewrite | Now imports and renders `<DecisionCommandCenter />`. Old greeting/tiles removed. |
| `frontend/src/components/shell/TopBar.tsx` | small | Crumb for `/` updated to "Decision Command Center". |
| `frontend/src/components/home/homeTypes.ts` | new | View-model types for the home page. |
| `frontend/src/components/home/homeData.ts` | new | `Promise.allSettled`-style adapter aggregating 11 endpoints into a single view model with per-source failure tracking. |
| `frontend/src/components/home/HomePanelStates.tsx` | new | `PanelShell`, `PanelUnavailable`, `PanelEmpty` shared primitives. |
| `frontend/src/components/home/DataFreshnessBadge.tsx` | new | Reusable freshness/provenance pill — `ok`/`stale`/`warning`/`unavailable` only; never invents a "live" state. |
| `frontend/src/components/home/HomeStatusStrip.tsx` | new | Above-the-fold 5-card status strip (Regime, Queue, Portfolio, Data, Governance). |
| `frontend/src/components/home/GovernanceStatusCard.tsx` | new | Always-visible governance card carrying `data-governance="true"`. |
| `frontend/src/components/home/DecisionQueuePanel.tsx` | new | Left-column triage list — mixes ops queue, pipeline warnings, recommendation warnings, incidents, breaches; ranked critical→warning→info. |
| `frontend/src/components/home/OpportunityRadarTable.tsx` | new | Centre column: desktop table + mobile cards. Source is the current recommendation's top-conviction weights joined with engine dispersion. |
| `frontend/src/components/home/ResearchAssistantPreview.tsx` | new | Non-interactive preview of an assistant with hard-coded safety rules. |
| `frontend/src/components/home/PortfolioImpactCard.tsx` | new | Paper portfolio summary + empty state when no portfolio exists. |
| `frontend/src/components/home/ResearchEventsFeed.tsx` | new | Combined audit + news feed, decision-context only. |
| `frontend/src/components/home/ShadowResearchSnapshot.tsx` | new | RL/ML safety snapshot; loud warning if live pipeline influence is detected. |
| `frontend/src/components/home/SectorHeatmapPreview.tsx` | new | "Sector tilt" panel — labeled honestly as regime sector posture, not a market heatmap. |
| `frontend/src/components/home/SystemHealthMiniPanel.tsx` | new | Compact pipeline + integrations health rows. |
| `frontend/src/components/home/DecisionCommandCenter.tsx` | new | Main orchestrator — loads data, renders header, status strip, three-column main grid, and below-the-fold panels. |
| `frontend/src/__tests__/home-command-center.test.tsx` | new | 10 tests locking in safety + rendering contract. |
| `.claude/skills/finrlx-home-command-center/SKILL.md` | new | Project-local skill encoding the HOME-1 UX contract so future agents do not regress it. |

No backend files were modified. No new dependencies were installed.

## 4. Skills inspected / applied

| Skill | Status | How applied |
|---|---|---|
| `fintech-disclaimer-and-marketing-guard` | applied | Every CTA on the home page was checked against the forbidden-verb list. No "Trade / Buy now / Sell now / Execute / Connect broker / Auto-trade / AI pick / Guaranteed return" copy exists. Test `home page module — safe CTA enumeration` is a tripwire against future regressions. `<DisclaimerBanner />` continues to render at the shell footer (unchanged); the home page also carries an in-tree governance panel marked with `data-governance="true"`. |
| `recommendation-object-provenance` | applied at the UI layer | `DataFreshnessBadge` and `OpportunityRadarTable` always render the recommendation's `data_as_of` when available, and explicitly render "freshness unavailable" when missing. The home page does not modify pipeline-side provenance fields — it only renders them faithfully. |
| `backtest-hygiene-gate` | applied at the UI layer | `ShadowResearchSnapshot` always states "Research-only · backtests are not future performance" and surfaces shadow-only flags. Live pipeline influence triggers a loud warning. Hygiene rules themselves live in `app/services/backtest_hygiene.py` and were not modified. |
| `feature-flag-kill-switch` | considered, not added | The home page reuses existing endpoints (`/overview`, `/ops`, `/regime`, etc.) that are already gated by their respective UI flags. Hiding the redesigned home would mean reverting `page.tsx`; adding a transient `feature_home_command_center` flag would require backend + flag-context plumbing for marginal value. Documented as a follow-up. |
| `replay-determinism-harness` | not relevant | This phase touches no replay services, no `snapshot_data`, no Pydantic schemas. Replay determinism is unchanged. |
| `finrlx-home-command-center` (new) | created | Encodes the HOME-1 UX contract for future agents. Lists iron rules, forbidden patterns, and the four-question contract. |

Verification: `find .claude/skills -maxdepth 2 -type f -name 'SKILL.md'` lists
the new skill alongside the four pre-existing ones.

## 5. Data endpoints used

The home page calls **eleven** existing endpoints in parallel via
`Promise.allSettled`-equivalent error handling:

```
fetchOverview()            → /api/v1/overview
fetchCurrentRecommendation() → /api/v1/recommendations/current
fetchRegime()              → /api/v1/regime
fetchActivity()            → /api/v1/activity
fetchOps()                 → /api/v1/ops
fetchCurrentPaper()        → /api/v1/paper/current
fetchCurrentRisk()         → /api/v1/risk/current
fetchNews(false)           → /api/v1/news
fetchEngineComparison()    → /api/v1/engines/comparison
fetchDisagreement()        → /api/v1/engines/disagreement
fetchEvidence()            → /api/v1/engines/evidence
```

If any single endpoint fails:

- The error message is stored in `failures[<source>]`.
- The corresponding panel renders `PanelUnavailable` with the source error
  as a hint, rather than crashing.
- The other 10 panels render normally.
- The status strip and `DataFreshnessBadge`s mark the source as
  `unavailable`.

No new backend endpoints were added — the requirement to prefer frontend
aggregation over new backend surface area was honored.

## 6. Design package files inspected

```
design/handoff-package/HANDOFF.md
design/handoff-package/INDEX.md
design/handoff-package/overview.jsx
design/handoff-package/ops.jsx (referenced via Sidebar / Ops conventions)
design/handoff-package/hero.jsx
design/handoff-package/context.jsx
design/handoff-package/styles.css / tokens.css (via globals.css)
```

The design package's `overview.jsx` validates the structure used here:
triage table → portfolio health strip → regime strip → activity feed. The
implementation tracks that direction while explicitly demoting the
market-feel triage rhetoric in favor of decision-state framing.

## 7. UX decisions

- **Decision-first header.** Title says "Decision Command Center" (not
  "Overview"), with a subtitle that names the four-question contract.
  Greeting moves from h1 into the subtitle so it doesn't dominate.
- **Status strip = 5 cards, never more.** Regime, Needs review, Paper
  portfolio, Data health, Governance. Each card is at most three lines.
- **Three-column main grid on `lg`** (`lg:col-span-4 / 5 / 3`):
  decision queue + portfolio impact left, opportunity radar + research
  events centre, research assistant + governance + sector tilt right.
- **Mobile order** (vertical stack):
  1. Header + status cards (2-col).
  2. Pipeline-warning banner.
  3. Decision queue.
  4. Portfolio impact (empty state if missing).
  5. Opportunity radar (cards path).
  6. Research events.
  7. Research assistant.
  8. Governance.
  9. Sector tilt.
  10. Shadow research / System health.
- **Tables → cards at `<md`.** The opportunity radar ships *both* paths
  (`hidden md:block` + `md:hidden`) and the test asserts both render
  simultaneously so a CSS regression cannot kill one of them silently.
- **No fake "live".** `DataFreshnessBadge` exposes one of four states:
  ok / stale / warning / unavailable. There is no "Live" pill.

## 8. Mobile behavior

- 390px width verified by Vitest happy-dom rendering (the `radar-cards`
  test asserts the mobile path is mounted alongside the desktop table; CSS
  hides one or the other by viewport).
- All home-page buttons satisfy the existing `min-h-11` touch-target lint
  gate (`src/__tests__/touch-targets.lint.test.ts` continues to pass).
- The mobile decision queue rows reuse the desktop layout but action buttons
  carry `min-h-11 md:min-h-0` so they meet the 44pt floor on touch
  devices.

## 9. Safety / governance wording decisions

- "Decision-support tool. Not investment advice." appears in the
  governance card subtitle.
- "Research only" / "No broker execution" appear in the governance card
  body **and** in the status strip's Governance card.
- "RL shadow-only" / "ML shadow-only" / "Live pipeline influence" are
  status rows in the governance card with semantic dot colors.
- If `ops.ml_ops.any_model_influences_live_pipeline === true` OR
  `ops.rl.live_pipeline_influence === true`, a red banner is rendered in
  the governance card body and the status strip's Governance card flips to
  "Review" (breach tone).
- Shadow research snapshot states: "Shadow research outputs do not feed
  broker execution. Backtests are historical and do not predict future
  returns."
- Sector heatmap renamed to "Sector tilt" with the explicit note "Tilts
  come from the regime model, not a market-wide scanner."
- Research assistant copy: "Source-grounded answers. AI does not trade,
  approve, or publish recommendations."

## 10. Empty / loading / error states

| Situation | Behavior |
|---|---|
| Whole-page load | `<PageLoading label="Loading command center…" />` |
| Whole-page fatal error | `<PageError title="Home unavailable" />` with hint to check backend |
| No current recommendation | Opportunity radar shows `"No active conviction signals."` empty state |
| No paper portfolio | Portfolio card shows `"No active paper portfolio yet."` + two safe CTAs (Try a template / Configure profile) |
| No ops queue items | Decision queue says `"Nothing requires review right now."` |
| No news | Research events feed degrades to audit-only |
| No regime data | Sector tilt shows `"No regime sector data."` |
| Single endpoint fails | Panel shows `PanelUnavailable` with the error as a hint |

## 11. Tests added

`frontend/src/__tests__/home-command-center.test.tsx` (10 tests):

1. Renders the governance/safety panel with canonical wording.
2. Page tree contains "Decision-support tool" and "No broker execution".
3. Page tree contains "Research only".
4. Shadow research panel is framed as shadow-only and not a live
   recommendation (Research-only / shadow-only / "Backtests are not future
   performance" all assertable).
5. No CTA on the page contains forbidden execution language (scans every
   `<a>` and `<button>`).
6. Opportunity radar renders both a desktop `radar-table` and a mobile
   `radar-cards` element so neither is silently dropped.
7. Freshness/provenance copy (`as of 2026-05-21 …`) is on the page when
   recommendation data is fresh.
8. Empty-state for the paper portfolio renders with a safe "Try a template"
   CTA when no portfolio exists.
9. Partial data failure: `fetchOps` + `fetchCurrentRecommendation` both
   reject — page still renders, governance still rendered, opportunity
   radar shows panel-level "unavailable" copy.
10. `homeData.ts` `ACTION_LABELS` contains zero forbidden execution
    patterns (source-level tripwire).

Existing tests still pass (37 total — see Verification below).

## 12. Verification

| Command | Result |
|---|---|
| `npm run typecheck` | PASS — no TypeScript errors |
| `npm run test:ci` | PASS — 37/37 tests across 9 files |
| `npm run build` | PASS — 27 static pages, `/` is 11.8 kB (122 kB first load) |
| `pytest` (backend) | not run — no backend files changed |
| Browser screenshot | not captured — local Next.js dev server was not started in this session |

Raw command outputs are stored in
`DOCS/handoff/PHASE_HOME1_LOCAL_VERIFICATION_EVIDENCE.txt`.

## 13. Honest limitations and follow-ups

- **No browser screenshots captured.** Verification stopped at typecheck +
  unit test + production build. A follow-up task should start the dev
  server (`npm run dev`) and capture 390 px / 768 px / 1440 px screenshots.
- **No e2e smoke added.** The repo has a Playwright config at
  `frontend/playwright.config.ts`. A follow-up could add a 390 px and
  1440 px smoke at `/` asserting the governance marker and a radar element.
- **No TopBar command palette wired.** `cmdk` is installed but the TopBar
  search remains a static pill. Wiring it to a Cmd/Ctrl+K palette over
  routes + recent tickers is a clean follow-up.
- **No `feature_home_command_center` flag.** Documented in §4. If beta
  testers need a fast revert, the cheapest path today is reverting
  `page.tsx`. A real flag is a small follow-up.
- **Opportunity radar is *not* a market-wide scanner.** It reuses the
  current recommendation's top-conviction weights. That is honest, not
  hidden — the panel subtitle says so. A real screener endpoint would be a
  separate phase.
- **Research assistant has no backend.** Prompt chips are disabled
  buttons. Wiring an actual assistant ships in a later phase.
- **Production deployment was not verified.** Build succeeds locally; the
  deployed URL was not visited.

## 14. Review package guidance

To package only the HOME-1 deliverables for review:

```powershell
# From repo root
$dest = "DOCS/handoff/_phase_home1_review_package"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

$paths = @(
  "frontend/src/app/page.tsx",
  "frontend/src/components/shell/TopBar.tsx",
  "frontend/src/components/home",
  "frontend/src/__tests__/home-command-center.test.tsx",
  ".claude/skills/finrlx-home-command-center/SKILL.md",
  "DOCS/handoff/PHASE_HOME1_DECISION_COMMAND_CENTER_REPORT.md",
  "DOCS/handoff/PHASE_HOME1_LOCAL_VERIFICATION_EVIDENCE.txt"
)

foreach ($p in $paths) {
  if (Test-Path $p) {
    $target = Join-Path $dest $p
    New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
    Copy-Item -Recurse -Force $p $target
  }
}
Write-Host "Review package ready under $dest"
```
