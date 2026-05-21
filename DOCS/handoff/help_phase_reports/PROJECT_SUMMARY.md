# Help Center — Project closing summary

**Project:** In-app Help center for FINRLX
**Completed:** 2026-05-22
**Branch:** main (every phase committed and pushed)

## What was built

A complete in-app Help section at `/help` for the FINRLX decision-intelligence platform, integrated with contextual entry points throughout the workspace.

## Scope shipped

### Information architecture (Diátaxis-tagged)

- **Landing** (`/help`) — search, 9 area cards, "Looking for something specific?" tips block.
- **Getting started** (4 tutorials) — tour, first recommendation, profile, dashboard reading.
- **Concepts** (8 explanations) — weight-centric pipeline, universe and features, agents and engines, regimes and turbulence, risk overlays, backtest vs. paper vs. live, governance and audit, known pitfalls.
- **How-to guides** (11 recipes) — run a backtest, compare engines, promote to paper, defer / save thesis, edit a policy, investigate a breach, replay a decision, manage your universe, export research data, set up an integration, re-run the wizard.
- **Reference** (19 pages) — 4 catalogues (status chips, policy controls, metrics, REST API) + 15 per-route reference pages mirroring the live workspace.
- **Glossary** — ~50 alphabetical terms, anchor-per-term.
- **FAQ** — ~20 Q&A grouped by intent.
- **Troubleshooting** — 9 symptoms with symptom-first triage.
- **Changelog** — Keep-a-Changelog seed with 3 launch entries.
- **Disclaimers & legal** — bridges to /terms, /privacy, /disclaimer.

### Engineering

- **Stack:** Next.js 15 App Router + MDX (`next-mdx-remote`) + remark-gfm + rehype-slug + rehype-autolink-headings.
- **Content:** 48 MDX files under `frontend/src/content/help/`, ~25,000 words total.
- **Components:** 9 help-specific React components — `HelpShell`, `HelpSidebar`, `HelpLandingBody`, `PageHeader`, `Callout`, `Term`, `HelpLink`, `DiataxisBadge`, `Updated`, `Annotated`, plus the `HelpSearch` client component.
- **Search:** Build-time index over every page's title, summary, area, body excerpt; client-side weighted scoring with multi-term substring matching; serialized into the landing-page HTML (no separate fetch).
- **Screenshots:** Playwright pipeline against the live deploy with a 25-second post-networkidle wait (the hard-learned rule from the prior project); 14 captures committed to `frontend/public/help/screenshots/`.
- **Annotations:** Numbered SVG callout overlays on top of PNG screenshots; `<ol>` legend in `<figcaption>` linked via `aria-describedby` (W3C ARIA15-compliant); 6 pages annotated.

### Contextual entry points

- **Global `?` button** in the TopBar of every page → `/help`.
- **21 in-page HelpLinks** wired into:
  - Home — Decision Command Center title.
  - Decision — after Promote-to-paper and after Defer-decision actions.
  - Policies — page title + every policy-control category heading + inline "How to edit a policy".
  - Universe — page title + inline "How to manage your universe".
  - Backtests — page title + inline "How to run a backtest".
  - Risk — page title + Exposure section heading.
  - Replay — page title.
  - Engine Comparison — page title.

### Tooling

- `npm run help:shots` — Playwright screenshot pipeline against live deploy.
- `npm run help:audit` — full audit: route reachability, in-page HelpLink counts, axe-core a11y on representative pages.

## Verification

Every phase exit checklist passed. The closing audit run reports:

- **Routes:** 48/48 return HTTP 200 on the live Railway deploy.
- **HelpLinks:** 21 in-page anchors across 8 in-app pages, plus the global `?` (total 22 contextual entry points, exceeding the strategic plan's 12).
- **a11y:** 0 critical / 0 serious / 0 moderate on the concept page; 1 critical found and fixed (`aria-controls` reference) on the landing page in this phase.
- **Build:** 75 static pages prerendered (was 28 before the project); first-load JS on `/help/[[...slug]]` is 6.71 kB.
- **Tests:** 41/41 unit + component tests pass; no regression.

## Phase reports

Detailed per-phase reports under `DOCS/handoff/help_phase_reports/`:

- `H-0_report.md` — Scaffold + global `?` button.
- `H-1_report.md` — IA skeleton (47 stub MDX pages).
- `H-2_report.md` — Concepts track + glossary populated.
- `H-3_report.md` — Reference track populated.
- `H-4_report.md` — Screenshot pipeline + annotated overlays.
- `H-5_report.md` — How-to guides + HelpLink wiring.
- `H-6_report.md` — Search, FAQ, troubleshooting, changelog.
- `H-7_report.md` — Live verification, a11y, closing.

## Strategic-plan adherence

Every section of the strategic plan presented and approved on 2026-05-21 was delivered:

- §B Information Architecture — every route in §B shipped.
- §C Contextual entry-point map — 12/12 highest-impact slots wired (10 in-page + global ? + sidebar of /help).
- §D UX/UI spec — design tokens used exclusively, no hard-coded values, dark + light parity, focus rings via existing `aria` patterns.
- §E Screenshot pipeline — 25-second wait honored; SVG annotations layered separately so re-captures do not invalidate legends.
- §F 7-phase work plan — every phase ran end-to-end, with the named skills, the exit checklists, and a committed report.
- §G Gate management — every phase pushed only after typecheck + lint + build + tests green; failures were caught (the H-3 MDX `<timestamp>` bug, the H-6 `aria-expanded` warning, the H-7 `aria-controls` violation) and fixed before advancing.

## Risks closed during execution

- ✅ The auth-gated screenshot risk identified up-front was avoided: the workspace renders demo data for public access on every captured page.
- ✅ The MDX-library risk was avoided: `next-mdx-remote` integrated cleanly with App Router.
- ✅ Pagefind was deferred in favor of an in-bundle index, which removed an entire deployment dependency without sacrificing UX.

## Maintenance handoff

Going forward:

- **Updating a help page:** edit the MDX under `frontend/src/content/help/`. Next build picks it up.
- **Refreshing screenshots:** `npm run help:shots`. Outputs land in `frontend/public/help/screenshots/`. Annotations live in MDX, not in the PNG.
- **Verifying the live deploy:** `npm run help:audit`.
- **Adding a new contextual `?`:** import `HelpLink` from `@/components/help/HelpLink` and place it next to a heading or action with `anchor="path/under/help"`.
