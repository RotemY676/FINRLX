# Phase H-3 Report — Reference track

**Date:** 2026-05-22
**Branch:** main
**Status:** ✅ COMPLETED

## Scope

Populate the **Reference** track: 4 top-level catalogues + 15 per-route pages. Reference pages are terse, lookup-oriented, and mirror the UI structure of the page they describe.

## What was written

### Top-level catalogues (4 pages)

| Page | Coverage |
|---|---|
| **Status chips** | OK / INFO / WARN / UNAVAILABLE semantics; data-freshness, regime, recommendation, engine, operational, preview chips; UNAVAILABLE pitfall. |
| **Policy controls** | CASH_FLOOR, CONFIDENCE_FLOOR (3 layers), EXPOSURE_SINGLE, EXPOSURE_SECTOR, TURBULENCE_THRESHOLD, TURNOVER_CAP — each with default, allowed range, unit, edit location, and editorial notes. |
| **Metrics** | Sharpe, Sortino, Calmar, max drawdown, turnover, volatility — formulas, common misreadings, rules of thumb. |
| **REST API** | Auth, profile, recommendations, backtests, policies, universe, workspace endpoints. Error contract. Versioning policy. Cross-referenced to `services/api.ts` endpoints from the codebase audit. |

### Per-route pages (15)

- **home** (Decision Command Center) — every panel of the dashboard.
- **decision** — evidence, disagreement, weights, positions, scenario controls, action bar.
- **comparison** — engine matrix, alignment, weight comparison, position detail, rationale.
- **replay** — available replays, replay detail, rationale at snapshot, positions at snapshot, pipeline-stage snapshots, actions.
- **backtests** — experiments table, promotion review, equity curve, configuration, provenance, actions.
- **paper** — performance summary, drift, holdings, warnings, event log.
- **risk** — exposure, concentration.
- **policies** — active breaches, per-control editors, audit trail.
- **universe** — universes list, asset detail, coverage, readiness, sector breakdown.
- **ops** — publication queue, data feeds, engines, breaches, incidents, audit trail.
- **integrations** — fundamentals / market data / news categories, per-integration status.
- **news** — what it is and what it isn't.
- **admin** (Research lab) — research data browser, dataset export (format notes).
- **profile** — identity, wizard answers, derived defaults, re-run.
- **templates** — the 5 seed templates with bundled universe / engine / policy.

## Bug fixed

The first build attempt failed on `/help/reference/status-chips` because MDX interpreted `<timestamp>` as an unclosed JSX tag.

**Fix:** wrapped angle-bracket placeholders in inline code (`` `<timestamp>` ``). Audited all reference pages for the same pattern; one remaining `<ticker>` reference was already HTML-entity-encoded. `<token>` in the API page is inside a fenced code block, which MDX does not parse.

## Verification

| Check | Result |
|---|---|
| `npm run typecheck` | ✅ clean |
| `npm run lint` | ✅ clean (zero warnings) |
| `npm run build` | ✅ 75 static pages prerendered. Every `/help/reference/*` route resolves. |
| `npm run test:ci` | ✅ 41/41 pass — no regression. |

## What lands next (H-4)

Screenshot pipeline: build a Playwright capture script that snapshots the 12 highest-value contextual entry points from the live workspace, with a 25-second wait before each capture. Render annotated `<Annotated>` components in the key reference / guide pages.

## Exit checklist

- [x] 4 top-level reference pages have substantive bodies.
- [x] 15 per-route reference pages mirror the UI structure of the live workspace (recon-verified).
- [x] Every policy control documented with default, range, unit, edit location.
- [x] Every endpoint in `services/api.ts` documented or grouped.
- [x] All cross-links resolve to existing pages.
- [x] MDX angle-bracket placeholder gotcha caught and remediated.
- [x] Typecheck + lint + build + tests green.
- [x] Phase report committed.

## Next step

Commit, push, proceed to H-4.
