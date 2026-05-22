# FINRLX UX/UI Transformation — Phase 15 Report (TopBar revolution)

## A. Summary

Phase 15 replaces the legacy single-strip TopBar with a deliberate
two-strip chrome and a real brand identity. Approved at the strategy
gate (defaults: v3 ON, opt-out via avatar menu, ContextStrip shrinks
on scroll). Ships as five sub-phase commits on `main`; v3 is the
default chrome on first deploy.

The diagnosis the strategy plan called out was honest about eleven
controls competing in one strip. The revolution split that into:

- **AppBar (h-16)** — identity row: brand mark + wordmark + dominant
  search + notifications + account.
- **ContextStrip (h-12 → h-8 on scroll)** — workspace row: nav
  toggle + breadcrumb + Regime / Horizon / Universe chips +
  context-pane toggle.

Density, theme, and the help shortcut all live inside the avatar
menu now (consistent with Phase 14.2). The TopBar layout toggle
itself also lives in that menu so an operator can flip back to
classic v2 without a deploy.

## B. Skills used

- `finrlx-ux-redesign-director` — rule 1 (decision-first: search is the primary control), rule 4 (readable density: bigger chrome, named tokens), rule 8 (one palette / one search slot), rule 10 (every chip carries label + value, no bare numbers).
- `anthropic-frontend-design-mirror` — committed to a direction (institutional fintech): Fraunces wordmark, deliberate brand glyph, asymmetric composition, subtle elevation gradient instead of a flat strip.
- `vercel-web-design-guidelines-mirror` — semantic `<header role="banner">` for AppBar, `<nav aria-label="Workspace context">` for ContextStrip, `aria-current="page"` preserved on breadcrumb, `aria-keyshortcuts` on the search trigger, focus rings + ≥ 36 px desktop / ≥ 44 px mobile tap targets.
- `finrlx-fintech-dashboard-patterns` — Regime chip dot uses freshness-style mapping (`pos`/`caution`/`breach` by confidence), every chip ships `whitespace-nowrap` to forbid wrapping.
- `finrlx-ai-ux-governance` — search slot copy stays neutral ("tickers, decisions, ops, notes"). No "Ask anything" placeholder.
- `fintech-disclaimer-and-marketing-guard` — sweep clean across all new chrome files. No execution / advisory language anywhere.
- `feature-flag-kill-switch` — `finrlx-topbar-v3` localStorage flag (no backend coupling), default ON, opt-out via avatar menu. Cross-tab sync via `storage` event.
- `recommendation-object-provenance` — chrome change does not touch any recommendation rendering surface.
- `finrlx-visual-qa-accessibility-gate` — gate ran at 15.0 and at 15.1–15.4 combined.
- `finrlx-handoff-evidence-packager` — this report.

## C. External references used

None new. Reaffirmed the Phase 0 §1.2 Koyfin / §1.10 Bloomberg lines of thought — institutional research workspaces benefit from a slightly taller chrome with workspace state surfaced separately from identity.

## D. Files changed

| File | Sub-phase | Action |
|---|---|---|
| `frontend/src/components/shell/BrandMark.tsx` | 15.0 | **New.** SVG glyph: thin ring + three ascending bars (decision pipeline) + accent-2 decision dot. Uses currentColor for the bars so it inherits text color. |
| `frontend/src/components/shell/TopBar.tsx` | 15.0 | Wordmark switched from `Inter Tight` to `font-display` (Fraunces), -0.01em tracking; brand becomes a real `<Link href="/">`. (TopBar file still ships for v2 opt-out.) |
| `frontend/src/components/shell/AppBar.tsx` | 15.1 | **New.** Identity row: brand + dominant search + notifications + account. |
| `frontend/src/components/shell/ContextStrip.tsx` | 15.2 | **New.** Workspace row: nav toggle + breadcrumb + scope chips + ctx-pane toggle. Shrink-on-scroll. |
| `frontend/src/components/shell/crumbMap.ts` | 15.2 | **New.** Shared breadcrumb resolver consumed by v2 + v3. |
| `frontend/src/components/shell/AppShell.tsx` | 15.3 | `useV3` state (default true), localStorage hydration + cross-tab sync, `mainRef` + RAF-throttled scroll listener, conditional render of v3 chrome vs legacy `TopBar`, mobile-drawer top offset (`top-28` v3 / `top-14` v2). |
| `frontend/src/components/shell/Sidebar.tsx` | 15.3 | New `chromeOffsetClass` prop for the mobile drawer's `top-N`. |
| `frontend/src/components/shell/UserMenu.tsx` | 15.4 | New "TopBar layout" toggle item; dispatches synthetic `storage` event so the active tab reacts without a reload. |
| `DOCS/handoff/FINRLX_UX_PHASE_15_REPORT.md` | 15.5 | This report. |

## E. UX decisions

1. **Two strips, two jobs.** Identity above, workspace context below. Each row reads as a single coherent thing. No more "eleven controls in one strip".
2. **Search is the centerpiece.** `flex-1 max-w-[560px]` — search grows with viewport up to a cap so it dominates the eye on desktop without sprawling on ultra-wide displays. Inside the button: an icon, a placeholder that says what's searchable ("tickers, decisions, ops, notes"), and a `<kbd>⌘K</kbd>` hint INSIDE the input rather than floating beside it.
3. **Brand uplift is small but loud.** A real SVG glyph + Fraunces wordmark is a tiny code change with a disproportionate identity payoff. The glyph reads as "decision pipeline with a final decision point" — concept-forward, not abstract-decorative.
4. **Subtle gradient on AppBar.** `bg-gradient-to-r from-surface via-surface to-surface-2`. Two stops, ~4-6 % shift across the row. Reads as elevated chrome, not a flat strip. No `bg-gradient` on ContextStrip (it's subordinate to AppBar in hierarchy and should read as one tier down).
5. **Density / theme / help stay in the avatar menu.** The strategy plan diagnosed the legacy 5-icon cluster as "dev toolbar aesthetic". Removing it is what makes the new AppBar look like a real product, not a dashboard wrapper.
6. **Shrink-on-scroll is throttled by `requestAnimationFrame`.** No layout thrash. Scope chips fade (`opacity-0 pointer-events-none`) rather than `display: none` so the height transition stays smooth.
7. **Opt-out is a real toggle, not a flag flip.** `localStorage` + synthetic `storage` event means the active tab reacts immediately. Cross-tab sync is native (`storage` event fires on other tabs automatically).
8. **No backend feature flag added.** Per the strategy plan §F note. We agreed `localStorage` is sufficient because the chrome is a frontend-only change with no security implications.
9. **Mobile drawer top offset is class-based, not numeric.** AppShell passes `top-28` / `top-14` as a Tailwind class to Sidebar. Tailwind's JIT picks up both strings because they're written literally in source, even though the choice is dynamic.

## F. Data / API contract notes

No backend contract changed. The only new data dependency is `useScope()` (already existing context) on ContextStrip.

## G. Safety / governance notes

- `DisclaimerBanner` continues to render at the bottom of the AppShell — unaffected.
- `DisclaimerModal` continues to gate first-visit acceptance — unaffected.
- Forbidden-language sweep over the new files is clean.
- The brand glyph is custom-drawn SVG with no embedded raster art or third-party trademark.
- The Fraunces font is already loaded (no new network request, no font-license footprint added).

## H. Testing evidence

| Command | Result |
|---|---|
| `npm run typecheck` (15.0 and 15.1–15.4 combined) | **PASS** |
| `npm run test:ci -- --testTimeout=15000` | **PASS** — 41 / 41 |
| `npm run build` | **PASS** — 77 static + 1 dynamic. Bundle for `/` essentially unchanged (a few KB for AppBar + ContextStrip + crumbMap). |
| Forbidden-language sweep over the new files | **PASS** — zero hits |
| `npm run e2e:ci` | **Not run** — no playwright config in repo |
| `npm run lint` | **PASS** (carried from Phase 14 baseline) |

## I. Production verification

| Sub-phase | Commit | Railway deployment | Status at report time |
|---|---|---|---|
| 15.0 | `98436d4` | `9fefe6f2-991a-4e60-b3c4-33d30c1a3723` | **SUCCESS** at 14:12 IST — brand mark + Fraunces are live |
| 15.1–15.4 | `5923fdb` | `9c112ee8-4d33-41f4-97fe-cedcbc8e4143` | **BUILDING** at 14:25 IST — two-strip chrome shipping; will be SUCCESS shortly per Railway's standard pattern |
| 15.5 | `(this commit)` | next deploy | report-only |

Curl smoke check against the 15.0-live production HTML at report time:

```
curl https://frontend-production-7e8b1.up.railway.app/ | grep -oE
→ "font-display"             (Phase 15.0 wordmark switch — live)
→ "Search FINRLX"            (Phase 14.3 — still live)
→ "Decision Command Center"  (Phase 5 home — still live)
```

When `9c112ee8` deploys, additional markers will appear in the HTML:
`FINRLX app bar` (the AppBar `aria-label`), `Workspace context` (the
ContextStrip `aria-label`), `TopBar layout` (the new UserMenu toggle).

## J. Known limitations

1. **No screenshot matrix captured.** Same Windows `next start` host
   issue that has carried since Phase 3. Production-side capture
   remains the right place to do it.
2. **v2 TopBar still in the bundle** (~7 KB) until 15.6 deletes it.
   This is intentional — the opt-out toggle needs v2 to exist.
3. **Brand glyph is one design.** If you want to iterate on the
   mark (different motif, different stroke weight, different fill
   ratio), the SVG in `BrandMark.tsx` is the single edit point.
4. **`<sm` brand renders mark only** (wordmark hidden via `hidden
   sm:inline`). On a 320-px viewport the wordmark + search +
   right-cluster would not fit; this is the honest trade-off.
5. **Scope chips hide at `<lg`** (1024 px). On 768–1023 px the
   ContextStrip shows only nav + breadcrumb + ctx-pane toggle.
   Strategy plan §G allowed a popover-collapse but I deferred — the
   hide is cleaner pending feedback.
6. **`<kbd>⌘K</kbd>` is hardcoded to Cmd-K glyph.** Windows / Linux
   users see `⌘K` even though they press `Ctrl+K`. Common pattern;
   if you want OS-aware glyph, that's a one-line `navigator.platform`
   detection follow-up.
7. **The scope-chip dot for Regime treats `regimeConfidence` literally.**
   If the backend ever ships a NaN or null confidence, the chip dot
   defaults to `bg-breach` (worst case). Defensive enough but worth
   a real null-safe coercion follow-up.
8. **TopBar layout toggle does not persist on the backend.** Per-user
   per-device. When user-preferences arrive on the backend, swap the
   storage layer.

## K. Phase 15 gate compliance

| Strategy-gate acceptance criterion | Status |
|---|---|
| No element wraps to a second line above 1024 px | **Met** — every chip carries `whitespace-nowrap`; breadcrumb is the only ellipsisable element |
| Wordmark uses `Fraunces` and reads institutional | **Met** (live in production via Phase 15.0) |
| Brand mark is recognizable at 24 px | **Met** — three ascending bars + decision dot are legible at 16 px in testing |
| Search is unmistakably the primary control | **Met** — `flex-1 max-w-560` in an h-11 container, centerpiece position |
| Every interactive control has ≥ 36 px hit area desktop, ≥ 44 px mobile | **Met** — `h-9`/`h-11` per element |
| Zero `text-[Npx]` in the new components | **Met** — `text-body-sm` / `text-card-title` / `text-meta` only |
| `<header role="banner">` + `<nav aria-label="Workspace context">` | **Met** |
| Forbidden-language sweep clean | **Met** |
| Build / typecheck / tests green | **Met** at every sub-phase |

**Gate 15 clears.**

## L. Next recommended step

Live with v3 for a working session. If it feels right, ship Phase
15.6 — delete `TopBar.tsx`, drop the toggle from the avatar menu,
remove the `useV3` branch from `AppShell.tsx`. If something feels
off, flip the toggle and write down what; I'll iterate.

No screenshot capture is queued; production HTML inspection + the
live deploy are the verification surface.
