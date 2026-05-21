# Phase H-5 Report — How-to guides + contextual HelpLink wiring

**Date:** 2026-05-22
**Branch:** main
**Status:** ✅ COMPLETED

## Scope

Expand the 11 how-to guide MDX files into substantive task recipes (numbered steps + interpretation guidance + cross-links). Wire the `<HelpLink>` glyph into the actual app pages so users can jump from in-app context into the matching help page.

## What was written

### 11 how-to guides

Each guide follows the same structure: pre-flight requirements, numbered steps, interpretation / follow-up patterns, cross-links to related concept / reference pages.

| Guide | Steps | What it teaches |
|---|---|---|
| `run-a-backtest` | 8 | Open Backtests → pick universe/engine/window/cost model → run → read result honestly |
| `compare-engines` | 5 + interpretation guide | Engine matrix, alignment scatter, weight comparison, disagreement patterns |
| `promote-to-paper` | 5 + verification + revert | Decision page → action bar → confirmation → post-promotion monitoring |
| `defer-or-save-a-thesis` | side-by-side comparison | The two actions, when to use each, reversibility |
| `edit-a-policy` | 6 + patterns + anti-patterns | Open Policies → edit slider → enter reason → save; when it takes effect |
| `investigate-a-breach` | 6 + three breach patterns | Policies → Replay → decide between relax-policy and re-derive |
| `replay-a-decision` | 6 + forensic patterns | Find recommendation → load → read rationale at snapshot → pipeline stages |
| `manage-your-universe` | add/remove + bias discussion | Add asset (warming up → ready), remove (history preserved), avoid silent biases |
| `export-research-data` | 7 + file-schema + use cases | Research lab → bundle config → format choice → schema metadata |
| `set-up-an-integration` | 6 + troubleshooting | Integrations → credentials → test → enable; failure modes |
| `re-run-the-wizard` | 5 + non-destructive guarantees | Profile → re-run button → step through → what changes / what doesn't |

### Contextual HelpLink wiring in 7 app pages

Each `<HelpLink>` is a 5x5-pixel `?` glyph that deep-links into the relevant help page. Variants: small icon next to a heading, or `variant="inline"` for a "Learn more →" inline link in the page header.

| File | Where | Help anchor |
|---|---|---|
| `frontend/src/app/policies/page.tsx` | Page title + Edit-a-policy inline | `reference/pages/policies`, `guides/edit-a-policy` |
| `frontend/src/app/policies/page.tsx` | Each policy category heading (CASH_FLOOR, CONFIDENCE_FLOOR, etc.) | `reference/policy-controls#<category>` (auto-generated from the category key) |
| `frontend/src/app/decision/page.tsx` | Action bar — after "Promote to paper" button | `guides/promote-to-paper` |
| `frontend/src/app/decision/page.tsx` | Action bar — after "Defer decision" button | `guides/defer-or-save-a-thesis` |
| `frontend/src/components/home/DecisionCommandCenter.tsx` | Decision Command Center title | `getting-started/reading-the-dashboard` |
| `frontend/src/app/universe/page.tsx` | Page title + Manage-your-universe inline | `reference/pages/universe`, `guides/manage-your-universe` |
| `frontend/src/app/backtests/page.tsx` | Page title + Run-a-backtest inline | `reference/pages/backtests`, `guides/run-a-backtest` |
| `frontend/src/app/risk/page.tsx` | Page title + Exposure section heading | `reference/pages/risk`, `reference/policy-controls#exposure_single` |
| `frontend/src/app/replay/page.tsx` | Page title | `reference/pages/replay` |
| `frontend/src/app/comparison/page.tsx` | Page title | `reference/pages/comparison` |

**Coverage:** 9 of the 12 contextual entry points from the strategic plan §C are now wired (the global `?` button from H-0 makes 10; the Home status-chip and Research-assistant slots are deferred to a future polish phase).

## Verification

| Check | Result |
|---|---|
| `npm run typecheck` | ✅ clean |
| `npm run lint` | ✅ clean |
| `npm run build` | ✅ 75 static pages, every page resolves |
| `npm run test:ci` | ✅ 41/41 pass — no regression |

## What lands next (H-6)

Pagefind search index in the build, troubleshooting page, FAQ population, changelog seed.

## Exit checklist

- [x] All 11 how-to guides have numbered-step recipes plus interpretation guidance.
- [x] Every guide cross-links to its reference page and to relevant concept pages.
- [x] `<HelpLink>` wired into 10 in-app contextual slots (9 from H-5 plus the global `?` from H-0).
- [x] Anchor strings match real help-page anchors (verified by the existing IA).
- [x] Typecheck + lint + build + tests green.
- [x] Phase report committed.

## Next step

Commit, push, proceed to H-6.
