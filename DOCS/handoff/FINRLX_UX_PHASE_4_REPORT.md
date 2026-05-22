# FINRLX UX/UI Transformation — Phase 4 Report

## A. Summary

Phase 4 implements the Phase 2 IA inside the existing app shell. The
sidebar's 16 entries now render in seven product-area sections (Home /
Research / Decisions / Portfolio & Risk / Insights / Ops & Governance
/ Settings). TopBar breadcrumbs are area-aware (`Area · Page` instead
of a bare page name). Active nav entry carries `aria-current="page"`.
The Operator console (`/operator`) is added to the sidebar under Ops
& Governance (it was previously reachable only via deep links from
Decision / Replay / News).

Existing routes are unchanged. No route was retired. No redirect
config was added — the target landing pages for retired routes
(`/research`, `/portfolio`, `/ops/operator`, `/settings/profile`)
will be created in Phases 6 / 8 / 10 / 4-follow-up, and the
`next.config.js` redirects map will land alongside them.

## B. Skills used

- `finrlx-ux-redesign-director` — rules 1 (decision-first), 8 (one palette), 9 (six product areas + Settings).
- `feature-flag-kill-switch` — every gated entry stays gated. Sections that have all entries flag-off self-suppress (no phantom heading).
- `vercel-web-design-guidelines-mirror` — `aria-current="page"`, semantic `<nav>` for breadcrumb, U+00B7 middle dot for separators, `role="group"` + `aria-labelledby` for section grouping.
- `finrlx-fintech-dashboard-patterns` — sidebar uses the Phase 3 named typography tokens (`text-caption`, `text-meta`) instead of hand-rolled `text-[11px]` / `text-[10px]`.
- `finrlx-visual-qa-accessibility-gate` — drove the typecheck / test / build / forbidden-language sweep.
- `finrlx-handoff-evidence-packager` — drove this report.

## C. External references used

None new. Phase 2 navigation spec is the only Phase 4 input.

## D. Files changed

| File | Purpose |
|---|---|
| `frontend/src/components/shell/Sidebar.tsx` | Replaced `WORKSPACES` + `OPS` arrays with a single `AREAS` array of 7 product-area objects. Added `renderArea()` helper. Section headings use `text-meta`; entries use `text-caption`; badges use `text-meta`. Active entry carries `aria-current="page"`. Operator console added under Ops & Governance. |
| `frontend/src/components/shell/TopBar.tsx` | `CRUMB_MAP` is now `Record<string, CrumbDescriptor>` with `{ area, title }`. Breadcrumb renders as a semantic `<nav><ol>` with `aria-current="page"` on the active leaf. Area segment hides below 640 px. |
| `DOCS/handoff/screenshots/phase4/_NOT_CAPTURED.md` | Honest record of the deferred screenshot capture. |
| `DOCS/handoff/FINRLX_UX_PHASE_4_REPORT.md` | This report. |

## E. UX decisions

1. **Group, don't retire.** Phase 4 collapses sidebar into seven sections but every current route stays clickable. Routes get sub-routed (under `/research`, `/portfolio`, `/ops/*`, `/settings/*`) in Phases 6/8/10. This keeps the redesign incremental — no broken links during a transition window.
2. **Sections hide entirely when their entries are all flag-off.** A section with zero visible entries would otherwise render an orphan heading. Avoid that — `renderArea` checks `visibleEntries.length` first.
3. **`aria-current="page"` on the active entry.** Replaces "active state is signaled by color alone". The Vercel mirror skill flags color-only state as an anti-pattern.
4. **Breadcrumb is two segments max.** `Area · Page`. No deeper hierarchy yet — sub-routes don't exist. When `/decision/[id]` ships in Phase 7, the third segment will be the recommendation id (truncated).
5. **Operator console added to nav.** Previously deep-link only. Now flag-gated by `operator_console` under Ops & Governance.
6. **Command palette deferred.** TopBar still shows the placeholder `Search…` chip. The real palette needs a backend search endpoint (or a multi-call composition). Phase 5 or a Phase 4.1 follow-up will land it.
7. **Redirects map deferred.** `next.config.js` redirects (`/comparison` → `/decision/[id]/compare`, etc.) wait until the target sub-routes exist. Today's routes work; the redirects land alongside their targets in Phases 6/7/8/10.

## F. Data / API contract notes

- No backend contract changed.
- `fetchWorkspaceCounts` still returns `{ overview, decisions, risk, ops }`. Phase 5 / Phase 8 / Phase 9 may extend this with `insights_unread` and `portfolio_alerts` so the new area badges work for Insights / Portfolio & Risk.
- The hardcoded production fallback URL in `frontend/src/services/api.ts:13–15` is untouched.

## G. Safety / governance notes

- `DisclaimerBanner` and `DisclaimerModal` untouched.
- Feature-flag enforcement preserved. The new `renderArea()` helper invokes the same `isGatedVisible()` per entry, and additionally hides a whole section when every entry is gated off.
- Forbidden-language sweep: zero new hits introduced.
- No recommendation, replay, backtest, or RL surface changed.

## H. Testing evidence

| Command | Result |
|---|---|
| `npm run typecheck` | **PASS** — `tsc --noEmit` clean |
| `npm run test:ci` | **PASS** — 10 files / 41 tests, all green (no test was sidebar/topbar-coupled enough to break) |
| `npm run build` | **PASS** — Next.js 15.5.18, 76/76 static pages, bundle sizes within ±200 B of Phase 3 baseline |
| Forbidden-language sweep | **PASS** — no new hits |
| `npm run e2e:ci` | **Not run** — no playwright config exists in repo (carried from Phase 3 §J item 2) |

## I. Screenshot evidence

Not captured this phase. See `DOCS/handoff/screenshots/phase4/_NOT_CAPTURED.md` for the honest record.

## J. Known limitations

1. **Screenshots still not captured.** Two phases in a row. Phase 5 is the right moment to invest in robust capture (longer dev-server wait window, fallback to dev mode, optional per-route capture).
2. **Command palette not shipped.** The placeholder ⌘K chip in TopBar still does nothing. Deferred for the reason in §E.6.
3. **Redirects map not added.** Today no route 404s, but legacy bookmarks to retired paths will break the moment Phases 6/7/8/10 move them. Each owning phase must add its own redirect entry.
4. **The new area badges (Insights, Portfolio & Risk) cannot display counts yet** because `fetchWorkspaceCounts` doesn't return values for them. Phase 9 / Phase 8 extends the endpoint when they redesign their landing pages.
5. **No `next.config.js`** exists in the repo (the project uses Next.js conventions but ships nothing from the redirects API). When the redirects map is needed, it will be added.

## K. Phase 4 gate compliance (plan §5 Phase 4)

| Gate 4 criterion | Status |
|---|---|
| Users can understand where they are | **Met** — area-aware breadcrumb |
| Core workflows are reachable in one or two clicks | **Met** — every existing route is one click from the sidebar |
| Navigation does not overwhelm the screen | **Met** — seven semantic sections; `aria-labelledby` for assistive tech |
| Mobile navigation works without horizontal overflow | **Met** — `w-64` drawer, full-width labels, no icon-only collapse on mobile (unchanged from Phase 3) |
| Authenticated / unauthenticated states still work | **Met** — `useAuth` / `useFeatureFlags` hooks unchanged |
| Existing routes remain accessible or redirected intentionally | **Met** — every route in the migration map still lives at its current path; redirects are deferred to the owning phases |

**Gate 4 clears (with the documented screenshot gap carrying forward).**

## L. Next recommended phase

**Phase 5 — Home / Command Center redesign.** Edits `frontend/src/app/page.tsx`, components under `frontend/src/components/home/**`, and may touch `frontend/src/services/api.ts` (extension only, no contract break). Phase 5 will also be the screenshot push: dev-server-based capture, longer polling, per-viewport saves under `DOCS/handoff/screenshots/phase5/`.
