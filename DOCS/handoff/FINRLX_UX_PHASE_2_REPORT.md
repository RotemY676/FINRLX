# FINRLX UX/UI Transformation — Phase 2 Report

## A. Summary

Phase 2 locks the information architecture and navigation model. The
current 16-entry flat sidebar collapses into 7 product areas
(Home / Research / Decisions / Portfolio & Risk / Insights / Ops &
Governance / Settings). Every existing route has a target home with a
documented redirect. A command palette, breadcrumb model, and mobile
drawer are specified. Five open IA questions from Phase 1's playbook are
resolved. **No product code changed.** Phase 4 implements this spec.

## B. Skills used

- `finrlx-ux-redesign-director` (rule 9 six product areas; rule 8 one palette; rule 1 decision-first).
- `finrlx-fintech-dashboard-patterns` (per-area workspace shape).
- `feature-flag-kill-switch` (every gated entry stays gated).
- `fintech-disclaimer-and-marketing-guard` (area name language).
- `vercel-web-design-guidelines-mirror` (`aria-current="page"`, semantic nav, accessibility contract).
- `recommendation-object-provenance` (preserves `/decision/[id]` route shape).
- `finrlx-handoff-evidence-packager` (this report).

## C. External references used

None new in Phase 2. The benchmark synthesis from Phase 0 §1 (TradingView's primary-workflow accessibility, Koyfin's professional command center, Bloomberg's command palette) informed the seven-area decision and the palette spec.

## D. Files changed

| File | Purpose |
|---|---|
| `DOCS/handoff/FINRLX_UX_PHASE_2_INFORMATION_ARCHITECTURE.md` | Six product areas + Settings; user jobs; layout patterns; principles; redirect plan. |
| `DOCS/handoff/FINRLX_UX_PHASE_2_ROUTE_MIGRATION_MAP.csv` | 29-row table mapping every current route to a target area / path / disposition / redirect mechanism / owning phase. |
| `DOCS/handoff/FINRLX_UX_PHASE_2_NAVIGATION_SPEC.md` | Sidebar / TopBar / mobile drawer / command palette / breadcrumb / sub-nav contracts. |
| `DOCS/handoff/FINRLX_UX_PHASE_2_REPORT.md` | This report. |

No `.tsx`, `.ts`, `.css`, `.py` files touched.

## E. UX decisions

1. **Exactly seven top-level entries.** Anything else hides in sub-nav or under Settings.
2. **`/decision` stays as a redirect, not a list.** `/decision/[id]` is the canonical per-recommendation route. Phase 7 implements both.
3. **Comparison and replay collapse into Decisions sub-tabs.** Legacy routes 308-redirect.
4. **News becomes Insights.** Decision-linked event feed, not raw RSS.
5. **Risk and Paper move under `/portfolio`.** Tabbed landing with Paper / Risk / Scenario.
6. **Admin renames to `/ops/lab`.** Desktop-only gate preserved.
7. **Operator console under Ops as a sub-route.** Stays operator-only.
8. **Command palette is a Phase 4 deliverable.** The admin palette is the seed.
9. **Canonical name for shadow research lane: "Research-only"** in user-facing copy; "shadow lane" stays in backend / internal docs.
10. **No routes deleted.** All retired / moved routes get a 308 redirect.

## F. Data / API contract notes

No API contract changed. Two backend extensions noted as Phase 4 / Phase 5 follow-ups:

- `fetchWorkspaceCounts` should learn to return `insights_unread` and `portfolio_alerts` so the sidebar badges work for Insights and Portfolio & Risk.
- `/api/v1/search` (or equivalent) is needed for the command palette ticker / recommendation search. Currently no such endpoint exists. Phase 4 will either add it or compose the palette out of existing endpoints (`/universe`, `/recommendations/list`, `/operator/analyses`).

## G. Safety / governance notes

- The `/admin` desktop-only gate is preserved when the route renames to `/ops/lab`.
- `operator_console` flag remains required to see `/ops/operator`.
- Operator console copy stays operator-only — `finrlx-ai-ux-governance` rule.
- Disclaimer banner unaffected (still in `AppShell`).
- Feature-flag rules unchanged. Sidebar gates per area: an area entry hides when all its sub-routes are flag-off.

## H. Testing evidence

Phase 2 is documentation only. No automated tests apply. Manual checks performed:

- Counted current routes (25) against the IA migration map (29 rows including new `/research`, `/research/[ticker]`, `/portfolio`, `/decision/[id]`).
- Verified every current route appears in the migration map.
- Verified every target area in the IA doc has a primary user job sentence.
- Verified `recommendation-object-provenance` constraint (per-recommendation deep linking) is preserved by the `/decision/[id]` plan.

## I. Screenshot evidence

None — documentation only. Screenshot matrix becomes mandatory at Phase 3.

## J. Known limitations

1. **`/feedback` placement is not locked.** Phase 4 will decide whether it stays at the root (clearer for beta testers) or moves to `/settings/feedback`. The migration map records both options.
2. **`/backtests` placement** — currently parked under Research per the migration map. Phase 6 may move it under Ops & Governance instead if it turns out to be more ops-oriented than research-oriented. Either way the route stays accessible via redirect.
3. **Command palette backend** — there is no `/api/v1/search` endpoint today. Phase 4 has two options (build endpoint vs compose from existing endpoints); Phase 4 must decide before implementing.
4. **Help center placement** — moved under Settings as `/settings/help`. The TopBar `?` icon will keep linking to `/help` via a redirect; if that proves disorienting in testing, Phase 4 can revert.
5. **Saved views section** in the sidebar is preserved as-is. Phase 4 may revisit its grouping (one global section vs per-area subsections).
6. **No user testing has been done** on the seven-area model. We are confident it is better than the current 16-entry list, but Phase 12 / Phase 13 should validate with real users.

## K. Phase 2 gate compliance

See `FINRLX_UX_PHASE_2_INFORMATION_ARCHITECTURE.md` §8. All five Gate 2 requirements met.

**Gate 2 clears. Proceeding to Phase 3 — design system foundation.**

Phase 3 begins editing code: `frontend/src/app/globals.css`,
`frontend/tailwind.config.ts`, and a handful of UI primitives under
`frontend/src/components/**`. Typography moves to the playbook §3.3 scale.
Semantic tokens for `stale`, `shadow-only`, `blocked`, `governance` get added.
Phase 3 will run the full visual-QA gate.
