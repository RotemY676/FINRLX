# Phase H-4 Report — Screenshot pipeline + annotated visuals

**Date:** 2026-05-22
**Branch:** main
**Status:** ✅ COMPLETED

## Scope

Build a Playwright-based screenshot capture pipeline that targets the live Railway deploy, with the hard-learned 25-second post-networkidle wait that the prior project missed. Author `<Annotated>` overlays on the highest-traffic reference pages.

## What was added

### Screenshot pipeline

- `frontend/scripts/help-screenshots.ts` — TypeScript script using Playwright. Launches headless Chromium, sets viewport 1440×900 at DPR 2, pre-seeds localStorage to dismiss the disclaimer modal, navigates to 14 targets, waits `networkidle` + 25 s, captures.
- `frontend/package.json` — `help:shots` script (`tsx scripts/help-screenshots.ts`); added `tsx` as a dev dependency.
- `frontend/public/help/screenshots/*.png` — 14 captured screenshots: home, decision, comparison, replay, backtests, paper, risk, policies, universe, ops, integrations, news, admin, help. Sizes range 352–704 KB.

### Annotated overlays added to 6 reference pages

Each overlay uses the `<Annotated>` component with numbered SVG callouts and an `<ol>` legend in `<figcaption>` (ARIA15-compliant).

| Page | Callouts |
|---|---|
| `reference/pages/home` | Global `?` button, data-freshness chip (UNAVAILABLE), current-recommendation chip, regime stat card, Research-assistant preview banner. |
| `reference/pages/decision` | Recommendation header, confidence gauges, action bar (Save / Promote / Defer), Compare & Replay buttons, Evidence narrative. |
| `reference/pages/policies` | Active-breach banner, CASH_FLOOR section, three CONFIDENCE_FLOOR layers (data, model, operational). |
| `reference/pages/universe` | Universes list, active universe detail, coverage panel, readiness pill, sector breakdown. |
| `reference/pages/backtests` | Experiments table, status pill, promotion-review block, metrics row, equity curve. |
| `reference/pages/replay` | Replay/Forensics header, active replay row, status pills, promoted recommendation row, Replay Detail timestamps. |

## The 25-second wait rule

Every capture waits `networkidle` first, then an explicit `await page.waitForTimeout(25_000)`. This is the lesson from the prior project: even after networkidle, recharts charts, framer-motion animations, and lazy-loaded content can still be settling. Without the wait, screenshots can miss chart bars or show empty cards.

## Verification

| Check | Result |
|---|---|
| `npm run help:shots` | ✅ 14/14 captured, 0 failed, against live Railway deploy. |
| Visual review of all 14 PNGs | ✅ Disclaimer dismissed; pages show real seeded demo data; charts rendered. |
| `npm run build` | ✅ 75 static pages, every help page resolves; new `<Annotated>` blocks render. |
| First-load JS for `/help/[[...slug]]` | 6.71 kB (unchanged) — annotations are static SVG, no JS bundle growth. |
| Live `/help` page rendering | ✅ Verified visually: area cards populated, sidebar shows full TOC, "Reference" card shows 19 pages. |

## What lands next (H-5)

Write the 11 how-to guides as substantive task recipes, and **wire the contextual `<HelpLink>` glyph** into the relevant app pages (Policies header for CASH_FLOOR / CONFIDENCE_FLOOR, Decision action bar, Home status chips, etc.) so users can jump from in-app context into the matching help page.

## Exit checklist

- [x] Playwright script captures all 14 public pages.
- [x] 25-second post-networkidle wait enforced.
- [x] Disclaimer modal dismissed via localStorage pre-seed.
- [x] 6 reference pages have annotated overlays with numbered legends.
- [x] `<Annotated>` component renders correctly in the build.
- [x] Screenshots committed under `public/help/screenshots/` (deployed by Railway).
- [x] Typecheck + build green.
- [x] Phase report committed.

## Next step

Commit, push, proceed to H-5.
