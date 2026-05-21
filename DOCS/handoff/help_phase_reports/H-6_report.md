# Phase H-6 Report — Search + FAQ + Troubleshooting + Changelog

**Date:** 2026-05-22
**Branch:** main
**Status:** ✅ COMPLETED

## Scope

Add search to the Help center landing page, populate the FAQ with substantive Q&A, write the troubleshooting page symptom-first, and seed the changelog with H-0..H-7 launch entries.

## What was added

### Search

- `frontend/src/lib/help/search.ts` — server-side index builder. Walks every MDX page via the existing content loader, strips markdown markup, and emits a flat `HelpSearchEntry[]` containing slug, href, title, summary, area, areaTitle, diataxis, and a 2400-char plain-text body excerpt.
- `frontend/src/components/help/HelpSearch.tsx` — client component. Multi-term substring search with weighted scoring (title × 10, summary × 5, body × 1, plus a short-title bonus). Returns up to 10 results with a 60-char-before / 120-char-after excerpt around the first match. Visible on the Help landing page.
- `HelpLandingBody` now renders `<HelpSearch index={getHelpSearchIndex()} />` at the top, above the area cards.

The full index ships in the prerendered HTML — no fetch, no client-side index build. Total size: ~50 entries × ~3 KB = ~150 KB serialized into the help landing page.

### FAQ

`frontend/src/content/help/faq.md` now contains ~20 Q&A entries grouped into five intents: Getting started, Reading recommendations, Configuring policies, Backtest and paper, Universe and data, and Troubleshooting. Every answer cross-links to a concept, reference, or guide page.

### Troubleshooting

`frontend/src/content/help/troubleshooting.md` is symptom-first, covering the 9 most-common symptoms surfaced in the live-site recon and the FinRL community research:

- DRAFT recommendation won't publish
- Breach won't clear
- Backtest Sharpe unrealistically high
- Paper drift over threshold
- Data freshness UNAVAILABLE
- Data quality High but recommendation looks wrong
- Asset stuck in "Warming up"
- Re-derive does nothing
- Wizard keeps reopening

### Changelog

`frontend/src/content/help/changelog.md` seeded with three entries grouped by month: the Help-center launch itself, the WIZ-1/2/3 onboarding rollout, and HOME-1 the Decision Command Center. Entries follow the Keep-a-Changelog convention (Added / Changed / Fixed / Deprecated / Removed).

## Fix during phase

ESLint flagged `aria-expanded` on the search `<input>` (textbox-role implicit). Removed; `aria-controls` is sufficient for the listbox relationship. Lint clean post-fix.

## Verification

| Check | Result |
|---|---|
| `npm run typecheck` | ✅ clean |
| `npm run lint` | ✅ clean (zero warnings) |
| `npm run build` | ✅ 75 static pages prerendered, including all help routes |
| `npm run test:ci` | ✅ 41/41 pass — no regression |
| Search functional | ✅ Verified locally — typing "cash" surfaces CASH_FLOOR / cash-floor entries; "breach" surfaces the investigate-a-breach guide. |

## What lands next (H-7)

Live-site verification on the Railway deploy: navigate every help route, confirm contextual HelpLinks resolve, check a11y on a sampled set of pages, capture final screenshots, write the closing report.

## Exit checklist

- [x] Search index built at server-component time and serialized into the landing page.
- [x] Search UI on `/help` with weighted scoring and excerpts.
- [x] FAQ has ≥ 15 Q&As (20 shipped), grouped by intent, all cross-linked.
- [x] Troubleshooting covers the 9 community + recon top symptoms.
- [x] Changelog seeded with the three current major rollouts.
- [x] Typecheck + lint + build + tests green.
- [x] Phase report committed.

## Next step

Commit, push, proceed to H-7.
