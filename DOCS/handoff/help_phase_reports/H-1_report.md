# Phase H-1 Report — Help Center IA Skeleton

**Date:** 2026-05-22
**Branch:** main
**Status:** ✅ COMPLETED

## Scope

Create every MDX file from the strategic plan's information architecture, with proper frontmatter (`title`, `summary`, `diataxis`, `area`, `updated`, `order`) and a short stub body so each route renders something meaningful while the full content lands in later phases.

## What was added

### 47 new MDX content files

| Area | Count | Files |
|---|---|---|
| Getting started | 4 | tour, first-recommendation, understanding-your-profile, reading-the-dashboard |
| Concepts | 8 | weight-centric-pipeline, universe-and-features, agents-and-engines, regimes-and-turbulence, risk-overlays, backtest-vs-paper-vs-live, governance-and-audit, known-pitfalls |
| Guides | 11 | run-a-backtest, compare-engines, promote-to-paper, defer-or-save-a-thesis, edit-a-policy, investigate-a-breach, replay-a-decision, manage-your-universe, export-research-data, set-up-an-integration, re-run-the-wizard |
| Reference (top-level) | 4 | status-chips, policy-controls, metrics, api |
| Reference (per-page) | 15 | home, decision, comparison, replay, backtests, paper, risk, policies, universe, ops, integrations, news, admin, profile, templates |
| Top-level | 5 | glossary, faq, troubleshooting, changelog, disclaimers |
| **Total** | **47** | + index.md from H-0 = 48 routes rendered |

Every file carries:
- `title`, `summary`, `diataxis`, `area`, `updated`, `order` frontmatter.
- A 2-paragraph stub body that orients the reader and previews what the full page will cover. No "Coming soon" placeholders — every page reads as a deliberate intro.

### Sidebar improvements

- `HelpSidebar.tsx` now sub-groups the per-route reference items under a collapsible `<details>` block labeled **Per-page reference**, so the top-level Reference items (Status chips, Policy controls, Metrics, REST API) are not visually drowned by 15 page entries.
- The `<details>` auto-expands when the current pathname is inside `/help/reference/pages/`.
- All page reference entries had their `order` bumped to 101–115 so they sort cleanly after the top-level reference items (1–4).

## Verification

| Check | Result |
|---|---|
| `npm run typecheck` | ✅ clean |
| `npm run lint` | ✅ clean (no warnings, no errors) |
| `npm run build` | ✅ 48 help routes prerendered. Total static pages: 75 (up from 28 in H-0). |
| `npm run test:ci` | ✅ 41/41 pass — no regression |

## What lands next (H-2)

Fill out the **Concepts** track with real explanatory content based on the FinRL-X research summary: weight-centric pipeline, universe and features, agents and engines (PPO/A2C/SAC/DDPG/TD3/ensemble), regimes and turbulence, risk overlays, backtest vs. paper vs. live, governance and audit, and known pitfalls. Populate the glossary with the ~35 terms from the research output.

## Exit checklist

- [x] Every URL in the strategic plan's IA (§B) returns 200 in the build output.
- [x] Every page has frontmatter with `title`, `diataxis`, `area`, `updated`, `summary`.
- [x] Sidebar shows the full TOC, grouped by area, with sub-grouping for per-page reference.
- [x] Per-area sort order is correct (top-level → per-route under collapsible).
- [x] Diátaxis badge is set on every page (tutorial / how-to / reference / explanation).
- [x] No "Coming soon" placeholders — every stub reads as deliberate.
- [x] Typecheck + lint + build + tests green.
- [x] Phase report committed.

## Next step

Commit, push, verify on Railway, proceed to H-2 (Concepts content).
