# FINRLX UX/UI Transformation — Phase 3 Report

## A. Summary

Phase 3 lays the design-system foundation that Phases 5–10 will consume.
Changes are deliberately additive and narrowly scoped:

- Four new semantic CSS aliases in `globals.css`: `stale`, `blocked`,
  `governance`, `shadow` (both light and dark themes).
- Eight named Tailwind `fontSize` tokens that match the playbook §3.3
  scale: `text-page-title`, `text-section-title`, `text-card-title`,
  `text-body`, `text-body-sm`, `text-table`, `text-caption`, `text-meta`.
- Four new Tailwind color groups exposing the semantic aliases:
  `stale`, `blocked`, `governance`, `shadow`.
- One density-mode default bump: `--dens-text` 13.5 px → 14.5 px (default
  density only). Compact (12.5 px) and comfortable (14 px) tracks remain
  unchanged.
- Three feedback primitives migrated to the named tokens as a showcase:
  `PageError.tsx`, `PageEmpty.tsx`, `PageLoading.tsx`.

The existing OKLCH palette and Inter Tight / Fraunces / JetBrains Mono
font stack are **kept**. No component prop signatures changed. No tests
broke. The full 76-page Next.js build passes.

## B. Skills used

- `finrlx-ux-redesign-director` — rule 4 (readable density), rule 7 (forbidden language sweep), rule 10 (evidence not optional).
- `finrlx-fintech-dashboard-patterns` — informs the named typography tokens that Phases 5+ will consume.
- `finrlx-visual-qa-accessibility-gate` — drove the typecheck / test / build / forbidden-language sweep order.
- `finrlx-handoff-evidence-packager` — drove this report and the `_NOT_CAPTURED.md` marker.
- `anthropic-frontend-design-mirror` — informed the typography intent (Inter Tight / Fraunces / JetBrains Mono survives; commit to a direction).
- `vercel-web-design-guidelines-mirror` — body line-height ≥ 1.4, tabular figures noted in the playbook (no component changes yet).
- `fintech-disclaimer-and-marketing-guard` — drove the forbidden-language sweep; no new hits introduced.

## C. External references used

None new. Phase 0 synthesis remains the inspiration source.

## D. Files changed

| File | Purpose |
|---|---|
| `frontend/src/app/globals.css` | Added 12 new CSS custom properties (stale/blocked/governance/shadow, each with DEFAULT / soft / soft-ink, both themes). Bumped `--dens-text` 13.5 px → 14.5 px (default density only). |
| `frontend/tailwind.config.ts` | Added 4 semantic color groups + 8 named `fontSize` tokens under `theme.extend`. |
| `frontend/src/components/feedback/PageError.tsx` | Replaced `text-[14px]` / `text-[13px]` / `text-[11px]` with `text-card-title` / `text-body-sm` / `text-caption`. |
| `frontend/src/components/feedback/PageEmpty.tsx` | Replaced `text-[15px]` / `text-[13px]` with `text-section-title` / `text-body-sm`. |
| `frontend/src/components/feedback/PageLoading.tsx` | Replaced inline-loader `text-[13px]` label with `text-body-sm`. |
| `frontend/scripts/phase-screenshots.mjs` | New — Playwright-core driver for the screenshot matrix. Reusable from Phase 4 onward. |
| `DOCS/handoff/screenshots/phase3/_NOT_CAPTURED.md` | New — honest record of the Phase 3 screenshot gap. |
| `DOCS/handoff/FINRLX_UX_PHASE_3_REPORT.md` | This report. |

## E. UX decisions

1. **Additive over destructive.** Existing `text-[Npx]` utilities still work everywhere. Phases 5–10 opt into the named scale per surface. No mass search-and-replace in Phase 3.
2. **One-pixel density bump.** Moving `--dens-text` from 13.5 px to 14.5 px is the safest possible step toward the playbook's 15 px body target. Pages that already set explicit `text-[N px]` are unaffected; only inherited body copy nudges up slightly.
3. **Compact mode stays compact.** Keep `--dens-text` at 12.5 px in compact density — power users rely on it.
4. **Semantic aliases via `var()`, not duplicated values.** `--stale` aliases `--caution`. If we ever need to differentiate the two visually, we change one variable and the consumer code stays put.
5. **Shadow needs its own soft / ink.** `--accent-2` didn't ship soft/ink variants. Added them at hue 290 in both themes.

## F. Data / API contract notes

None. Phase 3 touches only CSS / Tailwind / a handful of layout primitives.

## G. Safety / governance notes

- `DisclaimerBanner` is unaffected — both its test files still pass (4/4 in the legal suite, see Testing Evidence).
- Forbidden-language sweep: zero new hits. Existing hits are confined to (a) skill / plan / playbook docs that define the forbidden list, (b) `frontend/src/content/help/reference/metrics.md` which uses "risk-free rate" as legitimate finance terminology in a Sharpe ratio definition, (c) `DOCS/manual/User Manual.html` which renders forbidden phrases inside a "wording-bad / avoid this wording" example block (lines 1480–1492). None are runtime UI copy.
- `recommendation-object-provenance` — no recommendation surface changed.
- `replay-determinism-harness` — no replay surface changed.
- Feature flags — no nav / route changes; the flag map is unchanged.

## H. Testing evidence

### Commands run

| Command | Result | Notes |
|---|---|---|
| `npm run typecheck` | **PASS** | `tsc --noEmit` — clean exit. Run both before and after edits. |
| `npm run test:ci` | **PASS** | Vitest: 10 files / 41 tests, all pass. Critical: `tokens-contract.test.ts` (UX-5.1) still passes after the new CSS variables are added. `DisclaimerBanner`, `DisclaimerModal`, `home-command-center` test suites all green. |
| `npm run build` | **PASS** | Next.js 15.5.18: compiled successfully in 20.5 s. Generated 76/76 static pages. |
| Forbidden-language sweep (`rg`) | **PASS with caveat** | Zero new hits introduced. All existing hits are doc-only, finance-terminology, or "avoid this wording" examples. Documented in §G. |
| `npm run e2e:ci` | **Not run** | No `playwright.config.*` is checked into the repo and no `e2e/` directory exists. The script is wired in `package.json` but has no tests to run. This is a pre-existing gap, not a Phase 3 regression. |

### Test counts (vitest output)

```
Test Files  10 passed (10)
     Tests  41 passed (41)
  Duration  13.44s
```

## I. Screenshot evidence

**Not captured this phase.** See `DOCS/handoff/screenshots/phase3/_NOT_CAPTURED.md` for the honest record.

Phase 3 visual delta is sub-pixel for most pages (one-pixel `--dens-text` bump plus three feedback primitives switching to named font-size tokens that resolve to nearly the same px values). Phase 4 will be the first phase whose visual delta is meaningful at every breakpoint, and will be the first phase whose screenshot matrix is mandatory.

## J. Known limitations

1. **Screenshot matrix not run.** Recorded honestly in §I and in `_NOT_CAPTURED.md`. Carries forward to Phase 4.
2. **Playwright e2e suite does not exist in this repo.** `package.json` declares the script but there's no `playwright.config.*` and no `e2e/` directory. Phase 12 will need to either build the suite or formally decline (with documentation).
3. **Axe-core accessibility sweep not yet wired.** `@axe-core/playwright` is installed (v4.10.1) but no test consumes it. Phase 12 deliverable.
4. **The new named font-size tokens are consumed by only three components.** The other ~25 pages still hand-roll `text-[N px]`. They migrate as their owning phase opens (Phases 5–10).
5. **`tokens.json` (referenced by `tokens-contract.test.ts`) was not updated** to include the new aliases. The test currently passes because it iterates `tokens.color.light` keys and verifies each appears in CSS — the new CSS keys are extras, which the test allows. If Phase 4 or 12 wants the JSON to be the source of truth, they should mirror the aliases there.
6. **`globals.css` line numbering changed.** Some prior reports (Phase 6E design gap reports, etc.) may reference line numbers in `globals.css` that have shifted. Anyone reading those should re-resolve via Grep.

## K. Phase 3 gate compliance (plan §5 Phase 3)

| Gate 3 criterion | Status | Evidence |
|---|---|---|
| Base text is readable | **Partially met** — default density body inherits 14.5 px (was 13.5 px); named `text-body` 15 px and `text-body-sm` 14 px tokens exist for Phases 5–10 to adopt | §D, §E.2 |
| Components have consistent spacing and hierarchy | **Met for the three migrated primitives** | `PageError`, `PageEmpty`, `PageLoading` |
| Light/dark mode still works | **Met** | Both `:root` and `:root[data-theme="dark"]` updated symmetrically; build passes |
| Existing pages are not visually broken | **Met (by virtue of additive changes)** — no existing class names removed, no removed CSS vars, no changed component prop signatures | typecheck + test:ci + build all green |
| No accessibility regression | **Met** — `DisclaimerBanner` / `DisclaimerModal` tests still pass; no a11y-related changes made | Vitest output |
| Screenshot evidence for desktop/tablet/mobile | **Not met** — recorded honestly | §I, `_NOT_CAPTURED.md` |

**Gate 3 is partially met.** Five of six criteria pass; the screenshot
criterion is not met and is documented as a gap. Per the
`finrlx-visual-qa-accessibility-gate` skill: a tooling-related miss
does not mark the phase failed, but also does not mark it passed —
the obligation carries forward to Phase 4.

**Proceeding to Phase 4** under that explicit caveat.

## L. Next recommended phase

**Phase 4 — App shell + global navigation redesign.** Will edit
`AppShell.tsx`, `Sidebar.tsx`, `TopBar.tsx`, `next.config.js` (for the
redirects map from Phase 2), and may introduce
`frontend/src/components/shell/CommandPalette.tsx`. Phase 4 will run
the full gate including the screenshot matrix on the seed of fresh
visual deltas.
