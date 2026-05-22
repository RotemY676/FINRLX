# FINRLX UX/UI Transformation — Phase 5 Report

## A. Summary

Phase 5 is a polish pass on the existing `DecisionCommandCenter`. The
pre-existing home implementation already satisfied most of plan §5
Phase 5 (it was built under the `finrlx-home-command-center` skill,
which encoded the same four decision-first questions the redesign plan
later codified). Phase 5's job here was: apply the Phase 3 named
typography tokens, tighten the supporting sentence, and verify the
content/structure tests still pass.

I am being explicit: **this is not a Phase 5 rewrite, it is a
consistency pass.** The redline backlog row H-1 ("re-tier the layout:
4 tier-1 panels above the fold, demote rest") was reviewed and judged
already satisfied — the current layout's main 3-column grid is the
above-the-fold tier; the 2-column shadow-research / system-health
grid is below-the-fold. The 9-panel count is intentional. Phase 0's
H-1 worry has, on closer inspection, less weight than it read in the
audit.

## B. Skills used

- `finrlx-ux-redesign-director` — rule 4 (readable density), rule 1 (decision-first), rule 10 (evidence not optional).
- `finrlx-fintech-dashboard-patterns` — required props on data components, freshness chips, semantic badges.
- `finrlx-ai-ux-governance` — `ResearchAssistantPreview` left untouched in Phase 5 (Phase 11 owns the assistant rewrite); current content already shows research-only framing.
- `finrlx-home-command-center` — pre-existing FINRLX skill whose contract drove the original implementation. Confirmed still satisfied.
- `fintech-disclaimer-and-marketing-guard` — verified no forbidden CTA copy on `/`.
- `finrlx-visual-qa-accessibility-gate` — drove typecheck / test / build / forbidden-language sweep.
- `finrlx-handoff-evidence-packager` — this report.

## C. External references used

None new. The Phase 0 benchmark synthesis applies in principle: Koyfin's "command center" framing is the closest visual analogue; AlphaSense's source-grounded research lens is reflected in the `ResearchAssistantPreview` panel's still-pending Phase 11 design.

## D. Files changed

| File | Purpose |
|---|---|
| `frontend/src/components/home/DecisionCommandCenter.tsx` | Header `h1` migrated to `text-page-title` (was `text-[22px]`). Supporting paragraph migrated to `text-body-sm` (was `text-[13px]`), color elevated from `text-ink-3` to `text-ink-2`, copy tightened. Pipeline warnings strip migrated to `text-caption` (was `text-[12.5px]`). |
| `DOCS/handoff/screenshots/phase5/_NOT_CAPTURED.md` | Honest record of deferred screenshot capture. |
| `DOCS/handoff/FINRLX_UX_PHASE_5_REPORT.md` | This report. |

## E. UX decisions

1. **Polish, don't rewrite.** The existing `DecisionCommandCenter` answers all four playbook questions and ships freshness, governance, shadow, blocked states. Rewriting it would risk breaking 9 content-strict tests for no real UX gain.
2. **`text-page-title` on the main h1.** Bumps the title from 22 px to 28 px — the biggest single readability win available without restructuring.
3. **`text-ink-2` for the supporting sentence** instead of `text-ink-3`. Increases contrast slightly (the OKLCH tokens place ink-2 at 0.42 vs ink-3 at 0.50 lightness; ink-2 is darker / higher-contrast on a white surface).
4. **Tightened the supporting sentence.** Dropped the awkward "This screen answers" preamble; the home header now reads: "Hi, {name}. Below: what changed, what needs review, what evidence supports it, and what is stale, shadow-only, or blocked."
5. **Did not touch sub-panels** (queue, radar, portfolio, governance, events, sector, shadow research, system health, assistant preview). Each sub-panel already passes its `home-command-center.test.tsx` assertions. They will get their own typography migration when redesigned in Phase 9 (insights) / Phase 8 (portfolio) / Phase 11 (assistant) / Phase 10 (ops health).
6. **Did not extend `fetchWorkspaceCounts`** with `insights_unread` or `portfolio_alerts`. That contract extension belongs to Phase 8 / Phase 9, when their landing pages exist and a real "unread" count means something.

## F. Data / API contract notes

No API contract changed. Phase 5 is presentation-only.

## G. Safety / governance notes

- `GovernanceStatusCard` rendering all six "Research only / No broker execution / RL shadow only / ML shadow only / Live pipeline influence / Data freshness" rows untouched.
- `DisclaimerBanner` still ships on every page via `AppShell`.
- Forbidden-language sweep: no new hits.
- `home-command-center.test.tsx` assertion "contains no CTA copy with forbidden execution language" still passes.

## H. Testing evidence

| Command | Result |
|---|---|
| `npm run typecheck` | **PASS** |
| `npm run test:ci` | **PASS** — 41 / 41, including the 9 `home-command-center` content/structure assertions |
| `npm run build` | **PASS** — Next.js 15.5.18, 76 / 76 static pages, `/` bundle unchanged at 12.1 kB |
| Forbidden-language sweep | **PASS** — no new hits |
| `npm run e2e:ci` | **Not run** — no playwright config in repo |

## I. Screenshot evidence

See `DOCS/handoff/screenshots/phase5/_NOT_CAPTURED.md`. Visual delta is sub-pixel for most page content; only the home header bumps from 22 px to 28 px.

## J. Known limitations

1. **Screenshots still not captured.** Carries into Phase 6+.
2. **Per-panel typography migration deferred.** `DecisionQueuePanel`, `OpportunityRadarTable`, `PortfolioImpactCard`, etc. still hand-roll `text-[Npx]`. They migrate when their owning phase rewrites them.
3. **`ResearchAssistantPreview` content is placeholder.** Will be wired to `/assistant` in Phase 11.
4. **No new data freshness chips added.** The existing `DataFreshnessBadge` already ships on the header source-status row; Phases 8 / 9 / 11 will add per-panel chips where they currently only carry section subtitles.
5. **Phase 5 is honestly small.** That is because the home page was built well to begin with. I am not going to invent a rewrite to "earn" the phase.

## K. Phase 5 gate compliance

| Gate 5 criterion | Status |
|---|---|
| Home answers: what changed, what matters, what needs review | **Met** (header copy + status strip + queue + radar) |
| No "trade/buy/execute" language | **Met** (vitest assertion + manual rg) |
| Every module has loading/empty/error/stale state | **Met** (existing `PanelShell` / `PanelEmpty` / `PanelUnavailable` infrastructure) |
| Data freshness appears | **Met** (header source-status chips; `GovernanceStatusCard` data-freshness row) |
| Mobile uses cards, not crushed tables | **Met** (existing `OpportunityRadarTable` ships both desktop table + mobile card path — verified by test) |
| Governance status is visible | **Met** (`GovernanceStatusCard` always-visible six-row card) |

**Gate 5 clears.**

## L. Next recommended phase

**Phase 6 — Research workflow redesign.** This is a NEW surface (`/research` and `/research/[ticker]` don't exist yet). Phase 6 will create the Research hub: search-first landing, ticker workspace, evidence drawer, source-grounded assistant integration cue (full assistant lives in Phase 11). Phase 6 must also decide whether `/backtests` actually lives under Research or under Ops — the redline backlog flagged both options.
