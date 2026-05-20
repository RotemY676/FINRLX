# UX/UI Track — execution log

A running, evidence-first record of the UX/UI overhaul. Each sub-phase is a single section: what shipped, why, file inventory, gate results. Append-only; do not edit closed sub-phases.

**Track scope:** UX-1 Foundation → UX-2 Mobile refactor of 6 dense surfaces → UX-3 A11y baseline → UX-4 Visual polish → UX-5 iOS prep (PWA + bridging foundations).

**Locked product decisions (2026-05-20):**
1. Mobile bottom tabs: Overview / Decision / Replay / Paper + "More"
2. Accept = visible button only — no swipe (per NN/g contextual-swipe guidance)
3. Disclaimer = first-launch modal + persistent footer (continues MVP-5 pattern)
4. iOS path = PWA first; native Swift deferred to a later track

**Operating contract:**
- Auto commit + push after gates green
- Sub-phase reporting to user; no per-commit approval gates
- All existing gates (pytest, ruff, mypy, tsc, vitest, build, playwright) preserved
- New gates added progressively: multi-viewport playwright, visual regression, axe-core, touch-target lint, font-size lint, Lighthouse mobile

---

## UX-1.1 — viewport meta + mobile-first CSS baseline
**Date:** 2026-05-20
**Commit:** `d0c85e3`
**Status:** Closed

### What shipped
- `frontend/src/app/layout.tsx` — added Next.js `viewport` export with `width=device-width`, `initialScale=1`, `viewportFit=cover`, themeColor for light + dark.
- `frontend/src/app/globals.css`:
  - `html { -webkit-text-size-adjust: 100%; text-size-adjust: 100% }` blocks iOS Safari paragraph auto-zoom.
  - `body { -webkit-tap-highlight-color: transparent; overscroll-behavior-y: contain }` kills the tap-gray-flash and the rubber-band scroll bounce.
  - `@media (max-width: 767px) { input, select, textarea { font-size: 16px } }` blocks iOS focus-zoom on inputs (Safari's hard rule: <16px triggers zoom).
  - `.safe-area-{pt,pb,pl,pr}` utilities reading `env(safe-area-inset-*)` for notch / home-indicator awareness.
- `.gitignore` — added `.claude/settings.local.json`.
- `.claude/settings.local.json` (gitignored) — allowlists `WebSearch` and `WebFetch` for research agents on this project.

### Why
The audit (score 2/10) flagged "no viewport meta" as the single highest-impact issue: iPhone Safari was rendering this app at desktop scale, leaving every user zoomed-out by default. Forcing input font-size ≥ 16px on mobile prevents the disorienting zoom-on-focus that fintech apps consistently get flagged for in usability research. Safe-area utilities are prerequisite for the bottom-sheet ContextPane and bottom-tab nav coming in UX-1.3 and UX-2.

### Gates
| Gate | Result |
|---|---|
| tsc --noEmit | clean |
| vitest | 13 passed (4 files) |
| next build | 17 routes static (unchanged: `/universe` still ships) |
| playwright chromium | 10 passed |

### Out of scope (deferred)
- Actual mobile drawer for the sidebar — UX-1.2
- ContextPane → bottom sheet — UX-1.3
- Tailwind token fixes (`bg-canvas-elevated` etc.) — UX-1.4
- Touch target audit — UX-1.5

---

## UX-1.2 — Mobile drawer for the sidebar
**Date:** 2026-05-20
**Status:** Closed

### What shipped
- `frontend/src/components/shell/AppShell.tsx` — replaced the single `navCollapsed` toggle with two pieces of state: `desktopCollapsed` (≥md width swap) and `mobileOpen` (off-canvas drawer). `onToggleNav` reads `window.matchMedia("(max-width: 767px)")` at click-time and routes the toggle to the right one. ContextPane is wrapped in `hidden md:block` until UX-1.3 lands its bottom-sheet replacement.
- `frontend/src/components/shell/Sidebar.tsx` — single component now serves both modes via Tailwind responsive classes. Below md the aside is `fixed inset-y-0 left-0 top-11 z-30 w-64 -translate-x-full`, sliding in to `translate-x-0` when `mobileOpen`. At md+ the aside reverts to `static md:w-52 md:translate-x-0` and the `collapsed` prop swaps it to `md:w-14` exactly as before. Each nav link gets `min-h-11` on mobile (44pt HIG floor) and `onClick={onMobileClose}` so navigating dismisses the drawer.
- `frontend/src/components/shell/TopBar.tsx` — burger button: `aria-expanded`, `aria-label` ("Open navigation" / "Close navigation"), `aria-controls="primary-nav"`, hit target raised to `h-11 w-11`. Context-pane toggle hidden on mobile (the pane itself returns in UX-1.3).
- `frontend/tests/e2e/mobile-shell.spec.ts` — new spec, 375×667 viewport. Two tests: (1) burger toggle opens drawer (asserted via aria-expanded), backdrop click closes it; (2) no serious axe-core violations on `/` at mobile viewport.

### Why
The audit flagged this as worst-offender #2: at 375px width the existing `w-52` sidebar occupied 55% of the viewport with no responsive escape. The drawer pattern is from NN/g mobile navigation guidance — explicit nav toggle, opaque backdrop, dismiss on link tap. ARIA on the burger is the minimum for the Sidebar to be navigable via VoiceOver.

### Gates
| Gate | Result |
|---|---|
| tsc --noEmit | clean |
| vitest | 13 passed |
| next build | 17 routes (no size delta) |
| playwright chromium | **12 passed** (+2 new mobile-shell tests) |
| axe-core on `/` @ 375px | 0 serious violations |

### Out of scope (deferred)
- ContextPane bottom-sheet — UX-1.3
- Tailwind token fixes — UX-1.4
- Touch targets across the rest of TopBar, modals, action strips — UX-1.5
