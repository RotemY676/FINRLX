# Phase H-7 Report — Live-site verification + a11y + closing

**Date:** 2026-05-22
**Branch:** main
**Status:** ✅ COMPLETED

## Scope

Verify every help route resolves on the live Railway deploy, confirm contextual HelpLinks are present on the in-app pages, run an axe-core a11y audit on the landing and a representative subpage, fix any blocking issues, and write the project-closing summary.

## What was added

### Live-deploy audit script

- `frontend/scripts/help-audit.ts` — Playwright + axe-core. Probes all 48 help routes against the live URL, counts in-page HelpLinks on 8 app pages, runs WCAG 2.1 A/AA + best-practice a11y on `/help` and `/help/concepts/weight-centric-pipeline`, surfaces critical / serious / moderate violation counts.
- `npm run help:audit` — runs the script. Default base URL is the Railway production deploy; override via `HELP_AUDIT_BASE_URL`.

### a11y fix

Initial audit surfaced one critical violation on the help landing: `aria-valid-attr-value` on the search input. Cause: `aria-controls` referenced the results container's id, but the container only renders when there are results. With an empty query, the referenced id did not exist in the DOM, which is invalid per ARIA spec.

**Fix:** make `aria-controls` conditional — only present when `showResults` is true. One-character change, lint + build clean post-fix.

## Live-deploy verification results

Ran `npm run help:audit` against `https://frontend-production-7e8b1.up.railway.app`.

### Route reachability

```
Help routes:  48 probed, 48 ok, 0 failed.
```

All 48 help routes return HTTP 200. Full list:

- `/help` (landing)
- 4 × `/help/getting-started/*`
- 8 × `/help/concepts/*`
- 11 × `/help/guides/*`
- 4 × `/help/reference/{status-chips,policy-controls,metrics,api}`
- 15 × `/help/reference/pages/*`
- 5 × `/help/{glossary,faq,troubleshooting,changelog,disclaimers}`

### Contextual HelpLink counts (in-page anchors targeting `/help/*`)

| Page | Anchors |
|---|---|
| `/` Home | 1 |
| `/decision` | 2 |
| `/policies` | 10 |
| `/universe` | 2 |
| `/backtests` | 2 |
| `/risk` | 2 |
| `/replay` | 1 |
| `/comparison` | 1 |
| **Total** | **21** |

The policies page has the most (10) because every policy-control category heading carries its own anchor.

### Accessibility audit (axe-core, WCAG 2.1 A/AA + best-practice)

| Page | Critical | Serious | Moderate |
|---|---|---|---|
| `/help` (before fix) | 1 | 0 | 0 |
| `/help` (after fix, pre-deploy) | expected 0 | 0 | 0 |
| `/help/concepts/weight-centric-pipeline` | 0 | 0 | 0 |

After the next Railway deploy picks up the `aria-controls` fix, both pages are expected to be at zero critical / serious violations.

## Visual verification

Re-captured all 14 workspace screenshots against the live deploy via `npm run help:shots`. Manually inspected each in the file system:

- **Home** — `?` glyph visible next to "Decision Command Center" title; chips render with seeded demo data; Research-assistant preview panel labeled "Preview only".
- **Decision** — `?` glyphs visible after "Promote to paper" and "Defer decision" buttons in the action bar.
- **Policies** — `?` glyph next to "Policy Editor" title; "Learn more" inline link on the right; `?` glyph after every CASH_FLOOR / CONFIDENCE_FLOOR / DATA_FRESHNESS section header.
- **Universe** — `?` next to title; inline "Learn more"; sector breakdown and readiness chips render.
- **Backtests** — `?` next to title; experiments table populated.
- **Replay** — `?` next to title; available replays list populated.
- **Risk** — `?` next to title and next to the "Exposure" section heading.
- **Comparison** — `?` next to "Engine Comparison" title.
- **Help center** — search bar present; all 9 area cards populated with correct page counts (4/8/11/19/1/1/1/1/1).

## Closing summary — what the Help center now is

A single source of truth for FINRLX, organized using the Diátaxis framework (every page tagged in MDX frontmatter as `tutorial` / `how-to` / `reference` / `explanation`).

**By the numbers:**

- 48 MDX pages totaling ~25,000 words.
- 21 contextual `<HelpLink>` glyphs wired into 8 in-app screens, plus 1 global `?` button in the TopBar of every page.
- 14 live-deploy screenshots, 6 of them with annotated numbered callouts and `<ol>` legends.
- 1 build-time search index over every page's title, summary, area, and body excerpt, with client-side multi-term weighted scoring.
- 1 reproducible screenshot pipeline (`npm run help:shots`) and 1 reproducible audit pipeline (`npm run help:audit`).
- 8 phase reports documenting every decision and verification.

## Exit checklist

- [x] All 48 help routes return 200 on the live deploy.
- [x] All 8 app pages with HelpLinks show the expected anchor counts (21 total).
- [x] One critical a11y violation found and fixed (aria-controls reference).
- [x] Live-deploy screenshots re-captured and visually verified.
- [x] `help:audit` and `help:shots` scripts ready for ongoing maintenance.
- [x] Closing report committed (this file).

## Next step

Commit the audit script + the a11y fix, push, run the audit once more after deploy to confirm zero critical violations. **The Help center is now feature-complete and ready for production use.**

---

## Final re-audit (2026-05-22, post-deploy of the aria-controls fix)

Ran `npm run help:audit` against the live Railway deploy after the H-7 commit landed.

| Page | Critical | Serious | Moderate |
|---|---|---|---|
| `/help` | **0** | 0 | 0 |
| `/help/concepts/weight-centric-pipeline` | **0** | 0 | 0 |

Route reachability and HelpLink counts unchanged from the previous run (48/48 routes 200, 21 in-page anchors across 8 app pages). The `aria-controls` conditional fix landed cleanly — the Help center is now at **zero critical / serious / moderate a11y violations** on both audited pages.
