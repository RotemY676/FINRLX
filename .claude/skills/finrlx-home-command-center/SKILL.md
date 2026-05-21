---
name: finrlx-home-command-center
description: Encodes the UX contract for the FINRLX home page (`/`). Use whenever modifying frontend/src/app/page.tsx, anything under frontend/src/components/home/**, or surfaces that feed the home data adapter. Phase HOME-1.
type: project
---

# FINRLX Home / Decision Command Center

The home page is the operator's primary triage surface. It must answer four
questions within 5 seconds of load:

1. **What changed?**
2. **What requires review?**
3. **What evidence supports each item?**
4. **What is safe, stale, shadow-only, or blocked?**

This skill exists so future code edits do not regress the home page into a
generic market portal.

## When to invoke

- Changes to `frontend/src/app/page.tsx`.
- Changes to any file under `frontend/src/components/home/**`.
- Changes that touch endpoints feeding home data: `/overview`, `/regime`,
  `/activity`, `/ops`, `/recommendations/current`, `/paper/current`,
  `/risk/current`, `/news`, `/engines/comparison`, `/engines/disagreement`,
  `/engines/evidence`.
- Adding new "above the fold" widgets to the home page.
- Reviewing the home page for a release tag.

## Iron rules

1. **Decision-first.** The home page is a decision command center, not a
   market portal. No fake live-market scanner. No autonomous-AI framing.
2. **Governance is always visible.** Render `<GovernanceStatusCard />` (or an
   element carrying `data-governance="true"`) somewhere in the tree.
3. **No execution language.** Forbidden CTA labels: Trade, Buy now, Sell now,
   Execute, Connect broker, Auto-trade, AI pick, Guaranteed return.
4. **Safe CTA labels only.** Review evidence, Open decision, Compare engines,
   View risk, Monitor, Defer, Save thesis, Open paper portfolio, Open ops.
5. **Partial-failure resilience.** Home data uses `Promise.allSettled`. A
   single failing endpoint must produce a panel-level "unavailable" state,
   not crash the whole page.
6. **No fake freshness.** `DataFreshnessBadge` renders one of `ok`, `stale`,
   `warning`, or `unavailable`. Never label data "live" unless a real live
   source is responsible. Missing `as_of` → "unavailable".
7. **Tables become cards on mobile.** Opportunity radar ships both a `<md`
   card path and an `md+` table path. Do not compress desktop tables onto
   mobile.
8. **Touch target floor.** Buttons and links visible at <md must satisfy
   the existing `min-h-11` touch-target lint (see
   `src/__tests__/touch-targets.lint.test.ts`).
9. **Disclaimer remains.** The shell-level `<DisclaimerBanner />` is the
   compliance footprint. Do not remove or duplicate it on the home page.
10. **Shadow research is honest.** Any RL/ML surface on the home page must
    state research-only / shadow-only and never imply future performance.
11. **Live pipeline influence is loud.** If `ops.ml_ops.any_model_influences_live_pipeline`
    or `ops.rl.live_pipeline_influence` is true, the governance card and
    status strip must visibly flag it — do not soften.

## Forbidden patterns

- Building a "buy/sell/hold" CTA directly on the home page.
- Generating sample news/holdings/market data and rendering it as real.
- Hiding stale-data warnings to make the page look "cleaner".
- Adding a new top-level home widget without a corresponding empty state.
- Calling `await Promise.all([...home fetches])` instead of `allSettled`-
  equivalent partial failure handling.
- Pushing the governance card off the first screen on desktop or mobile.

## How to apply

When editing any home-page file:

1. Re-read the home page on desktop (`1440px`), tablet (`768px`), and
   mobile (`390px`). The decision queue and radar must be reachable
   before lower-priority panels.
2. Confirm the four-question contract above is still answered.
3. Run the home tests:
   ```bash
   cd frontend && npm run test:ci -- home
   ```
4. Run the touch-target lint:
   ```bash
   cd frontend && npm run test:ci -- touch-targets
   ```
5. If you add/rename a CTA, grep for it against the forbidden list above.
6. If you add a new data source, route it through `loadHomeData` so the
   partial-failure contract holds.

## Why

- Operators want to land, triage, and move on. A portal-style home is
  friction; a decision command center is the differentiator.
- Compliance and trust depend on a *predictable* statement of what FINRLX
  is and isn't. Soft language drifts; this contract is hard-coded here.
- The home page is the most-viewed surface; regressions are expensive.
