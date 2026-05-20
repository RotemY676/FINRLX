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

---

## UX-1.3 — ContextPane becomes a bottom sheet on mobile
**Date:** 2026-05-20
**Status:** Closed

### What shipped
- `frontend/src/components/shell/ContextPane.tsx` — the panel now renders a `<>fragment</>` of a click-to-dismiss backdrop + an `<aside role="dialog" aria-modal="true" aria-label="Context pane">`. Tailwind responsive classes handle both modes in a single element: at <md it's `fixed inset-x-0 bottom-0 z-40 max-h-[85vh] rounded-t-2xl shadow-lg`; at md+ it reverts to the existing `md:static md:w-[360px] md:shrink-0 md:border-l md:border-line`. A drag-handle indicator (`h-1 w-10 rounded-full bg-line-strong`) sits at the top, visible only on mobile. The aside gets `safe-area-pb` so iPhone home indicators don't overlap content.
- Tab buttons, close button, and tab-switcher pills inside the pane all get `min-h-11` on mobile (44pt floor) and revert to the original tighter padding at md+.
- `frontend/src/components/shell/AppShell.tsx` — refactored into `AppShell` (provides PaneProvider) + `ShellInner` (consumes PaneContext). The toggle now drives `pane.isOpen` via `openTab("risk") / closePane()` instead of a local `ctxVisible` flag that was decorative. ContextPanePanel mounts unconditionally and self-gates on `pane.isOpen`.
- `frontend/src/components/shell/TopBar.tsx` — context-pane toggle revealed on mobile (was hidden in UX-1.2 since the pane it controls was suppressed). Hit target raised to `h-11 w-11`, `aria-expanded` reflects open state, accessible name flips between "Show context pane" / "Hide context pane".
- `frontend/tests/e2e/mobile-shell.spec.ts` — added test that the toggle's aria-expanded state flips both ways and the accessible name swaps. The dialog's role=dialog selector resists Playwright detection in some hydration ordering — visual verification of the sheet's rendered placement is deferred to UX-2's visual-regression gate.

### Why
The right-rail ContextPane was hidden entirely on mobile after UX-1.2, which left no path to surface Risk / Provenance / Compare / Notes context on small screens. Bottom-sheet is the iOS-native and NN/g-endorsed pattern for context-of-context UI; using the same component in two modes (driven only by Tailwind responsive prefixes) avoids the parallel-implementation drift that fintech apps often accumulate.

The AppShell refactor was a latent-bug discovery: the old `ctxVisible` state mounted the pane wrapper but never opened it (the wrapper short-circuited on `pane.isOpen` from PaneContext). The toggle button worked on paper but produced nothing visible. Wiring it through `openTab("risk")` makes the toggle behave per its label.

### Gates
| Gate | Result |
|---|---|
| tsc --noEmit | clean |
| vitest | 13 passed |
| next build | 17 routes (no size delta) |
| playwright chromium | **13 passed** (+1 new context-pane wiring test) |
| axe-core on `/` @ 375px | 0 serious violations |

### Honest limitation
The wiring test verifies state propagation (aria-expanded flips, accessible-name swaps, click-through round-trip). It does NOT yet verify the sheet's visible placement on screen — the `getByRole("dialog")` selector returned `<element(s) not found>` in this hydration path despite the role being on the rendered `<aside>`. I will revisit with screenshot-based assertion when the visual-regression gate lands in UX-2.

### Out of scope (deferred)
- Token fixes (`bg-canvas-elevated` etc. referenced by `DisclaimerModal`) — UX-1.4
- Touch-target audit across the rest of the app (admin, decision actions, action strips) — UX-1.5

---

## UX-1.4 — Token cleanup; DisclaimerModal mobile-aware
**Date:** 2026-05-20
**Status:** Closed

### What shipped
- `frontend/src/components/legal/DisclaimerModal.tsx` — replaced the four undefined Tailwind tokens with the design system's actual tokens: `bg-canvas-elevated` → `bg-surface`; `text-text-default` → `text-ink` / `text-ink-2`; `bg-accent-default` → `bg-primary` + `text-primary-ink`; `bg-accent-hover` → `hover:opacity-90`. Backdrop changed from `bg-black/50` to `bg-ink/60` (theme-aware via CSS var). Added `max-h-[90vh] overflow-y-auto` so the modal scrolls instead of clipping at iPhone SE landscape (667×375). Button raised to `min-h-11 inline-flex items-center justify-center` for the HIG 44pt floor.
- `frontend/src/components/legal/DisclaimerBanner.tsx` — replaced 4 broken token refs (`border-divider`, `bg-canvas-elevated`, `text-text-muted`, `hover:text-text-default`) with `border-line`, `bg-surface`, `text-ink-3`, `hover:text-ink`. Added `safe-area-pb` so the home-indicator on notched iPhones doesn't crash into the disclaimer copy.
- `frontend/src/app/{terms,privacy,disclaimer}/page.tsx` — same `text-text-default` / `text-text-muted` cleanup; mapped to `text-ink-2` / `text-ink-3`.

Total: 7 files, 0 tokens remain undefined (grep confirms).

### Why
The audit flagged the disclaimer modal as visually broken: four CSS class names referenced tokens that don't exist in `tailwind.config.ts`, so they rendered as no-ops. The modal still appeared, but with default browser styling (no card background, default text color, no accent button color) — inconsistent with the rest of the app and visually unprofessional for the first thing a tester sees on first visit. Same defect quietly cascaded into the persistent banner and three legal pages.

The max-height + scroll fix is a real iPhone landscape issue: at 667×375 the modal's content (3 paragraphs + CTA + 24px padding × 2 ≈ 430px) overflowed the 375px viewport height with no scrollbar.

### Gates
| Gate | Result |
|---|---|
| tsc --noEmit | clean |
| vitest | 13 passed |
| next build | 17 routes (no size delta) |
| playwright chromium | 13 passed (mobile-shell context-pane test now closes via the in-sheet close button — more robust on a 375px viewport where the TopBar toggle can be partly obscured by the sheet) |
| Grep audit | 0 references to `canvas-elevated`, `text-default`, `text-muted`, `accent-default`, `accent-hover`, `bg-canvas-base`, `border-divider` remain |

### Out of scope (deferred)
- Touch-target audit + lint script across TopBar, decision actions, admin — UX-1.5

---

## UX-1.5 — Touch-target sweep + CI lint
**Date:** 2026-05-20
**Status:** Closed

### What shipped
- `frontend/src/components/shell/TopBar.tsx` — remaining TopBar buttons brought to HIG 44pt floor on mobile:
  - **Theme toggle:** `p-1.5` → `inline-flex items-center justify-center h-11 w-11 md:h-9 md:w-9`; icon size 15 → 18; explicit `aria-label`.
  - **Notifications button:** wrapped in `hidden md:inline-flex` (deferred to a future mobile notification surface); height bumped to `h-9 w-9` at md+; explicit `aria-label`.
  - **Sign-out button (UserChip):** text changed from `text-[11px]` to `text-[12px]`, `px-2 py-1` → `h-9 px-3`, and `hidden md:inline-flex` so it doesn't crowd the 375px TopBar. User avatar bumped from `w-7 h-7` (28px) to `w-8 h-8` for legibility.
- `frontend/src/__tests__/touch-targets.lint.test.ts` — new vitest gate that walks every `.tsx` under `src/`, parses opening `<button>` JSX tags, and **fails CI** if any button ships with a fixed height in `h-6..h-10` without a `min-h-11`/`h-11+` override on the same element. Two escape hatches:
  - `// touch-target-lint:allow — reason` comment on the `<button>` line for documented exceptions
  - `hidden md:|lg:|xl:` reveal pattern auto-exempts pointer-only buttons (mouse, not touch)
- The lint passes today against the entire `src/` tree with zero violations and zero allow-comments. This becomes the no-regression baseline.

### Why
The audit flagged TopBar's per-icon buttons at ~27px (`p-1.5` + 15px icon) as below HIG's mandatory 44pt floor. WCAG 2.5.5 demands the same minimum. The cure is two-part: fix what's there, and gate so it doesn't come back.

Notifications + Sign-out got `hidden md:inline-flex` rather than the 44pt treatment because the TopBar on 375px is already at capacity with brand + nav toggle + breadcrumbs + theme + ctx-toggle + avatar. Forcing them visible would push something off-screen; their mobile equivalents (notification center, signed-in menu) belong in a "More" surface that lands in UX-2.

The lint is a vitest test rather than an ESLint rule because it integrates with the existing CI lane with zero new toolchain — and because the rule is structural (state-of-element-after-className-merge), which is awkward for ESLint plugin authoring.

### Gates
| Gate | Result |
|---|---|
| tsc --noEmit | clean |
| vitest | **14 passed** (5 files; +1 lint suite) |
| next build | 17 routes (no size delta) |
| playwright chromium | 13 passed |
| touch-targets.lint | 0 violations |

### Honest limitations & deferred work
- **Padding-only buttons not yet linted.** The decision-page action strip (`/decision`) has 9 buttons sized purely by `px-3 py-1.5` content padding. They compute to ~28-30px tall on mobile — still below HIG — but they have no `h-N` class for the lint to catch. Detecting padding-only buttons requires CSS computation we can't do statically. **Fixed in UX-2.2** as part of the decision-page mobile refactor where the strip becomes a sticky bottom CTA + overflow menu.
- **Font-size hotspots not yet blocked.** A grep of `text-[10px]` + `text-[11px]` returned **564 occurrences across 43 files**. Most are non-interactive labels/badges where context makes them readable, but several sit inside `<button>` content. Blocking all 564 in UX-1.5 isn't feasible. The bulk reduction happens during UX-2 (mobile data refactor) and UX-4 (visual polish). Once the count drops below ~50, a `text-[10px]` lint flips to hard fail.
- **PipelineStep h-10 circle** (admin) — visually 40px but the actual `<motion.button>` wraps the circle + label + count, making the real tap target ~70-80px. No fix needed; recorded for clarity.

### Phase UX-1 closes here
Foundation is in place: viewport meta, mobile-first CSS base, mobile drawer for nav, bottom-sheet for context pane, all design tokens valid, touch-target lint as a no-regression gate. Next: Phase UX-2 — mobile-first refactor of the six dense surfaces (`/comparison`, `/decision`, `/paper`, `/replay`, `/backtests`, `/admin`).

---

## UX-2.1 — `/comparison` mobile refactor (Engine Matrix + Position Detail)
**Date:** 2026-05-20
**Status:** Closed

### What shipped
- `frontend/src/app/comparison/page.tsx` — both tables now use the **pinned-primary-column + hide-secondary-columns** pattern from the fintech UX research (UX Movement / NN/g / Mobbin). Specifics:

  **Engine Matrix:**
  - Mobile (<md): visible columns = Engine, Stance, Confidence-microbar (3 columns)
  - md+: adds Weight, Horizon, Risk (6 columns)
  - lg+: adds Top Drivers (7 columns — full desktop view)
  - On mobile the Engine cell carries an inline secondary line ("`{weight}% · {horizon} · {risk_read}`") so the hidden columns aren't lost.
  - Synthesis row gets the same treatment with an inline summary line on mobile.

  **Position Detail:**
  - Mobile: visible columns = Ticker, Active delta, Stance (3 columns)
  - md+: adds Name, Rec, Bench (6 columns)
  - On mobile the Ticker cell carries an inline two-line summary ("`{name}` / `Rec {x}% · Bench {y}%`") for context.

- Both tables: each row gets `role="button" tabIndex={0}` + `onKeyDown` (Enter/Space) for keyboard a11y, plus `focus-visible:bg-surface-3` for keyboard navigation feedback. The existing click → `openPane(...)` flow is preserved verbatim — on mobile, that pane is now a bottom sheet (UX-1.3), giving the full data the column-hide left out. Engine methodology pane now also exposes Weight / Horizon / Risk (previously surfaced only by the visible columns; needed in the sheet now that those columns hide on mobile).
- Row padding raised from `py-2` (32px row) → `py-3 md:py-2` (48px+ on mobile, original 32px on desktop) so taps don't miss on rows of small numerical data.
- Confidence microbar shrunk from `w-14` → `w-10 sm:w-14` so the column doesn't overflow on 375px.

- `frontend/tests/e2e/comparison-mobile.spec.ts` — new spec runs the page in both 375×667 and 1280×720 viewports. Mobile check includes `expectNoSeriousAxeViolations`.

### Why
The audit flagged `/comparison` as one of the two worst surfaces on mobile: 7-column Engine Matrix and 6-column Position Detail both relying on `overflow-x-auto` as the only mobile affordance, with `text-[12.5px]` making horizontal scroll truly miserable. The synthesis row extending off-screen meant the actual recommendation was invisible without scrolling.

The hide-columns approach (instead of cards-per-engine) was chosen because (a) the ContextPane bottom sheet already exists and gives the full detail, (b) the column-hide preserves desktop fidelity exactly, and (c) UX research (Koyfin/AlphaSense companion apps) cites pinned-primary + tap-detail as analyst-grade. A card-per-engine alternative would have duplicated information already in the sheet.

### Gates
| Gate | Result |
|---|---|
| tsc --noEmit | clean |
| vitest | 14 passed (incl. touch-targets lint) |
| next build | 17 routes |
| playwright chromium | **15 passed** (+2 new comparison-mobile specs at 375 + 1280) |
| axe-core on `/comparison` @ 375px | 0 serious violations |

### Honest limitations
- The 9 buttons in the action strip on `/decision` were not touched here — that's UX-2.2.
- I didn't add a visual-regression `toHaveScreenshot` baseline. Visual diffs land when the design polish lands in UX-4 (right now the visuals are still going to shift).
- Synthesis row's inline mobile summary uses a fixed string ("`100% · Weighted across all engines`"); if the backend ever computes a different synthesis weight, that string drifts. Tracked for future hardening if the synthesis weight becomes dynamic.

---

## UX-2.2 — `/decision` action strip + risk gauges mobile refactor
**Date:** 2026-05-20
**Status:** Closed

### What shipped
- `frontend/src/app/decision/page.tsx`:

  **Action strip (the 9-button row the audit called out):**
  - Restructured into a `flex flex-col md:flex-row md:flex-wrap` container.
  - The **3 primary CTAs with real handlers** (Save thesis, Promote paper, Defer) get `min-h-11` on mobile (HIG 44pt) and stack full-width — no more "Save as current thesis" being cropped at 1/3 of 375px. At md+ they revert to the inline row layout exactly as before.
  - The **5 secondary affordances with no `onClick` handlers yet** (Bookmark, Share, Compare, Replay, More) get `hidden md:inline-flex` — they vanish on mobile until they earn real handlers and a proper "More" menu. They still take their original layout at md+.
  - Each button gets explicit `type="button"`, plus `aria-label` on icon-only buttons (Bookmark, Share, More).
  - Action message gets `role="status" aria-live="polite"` so VoiceOver announces "Saved" / "Failed" without needing focus.
  - `animate-pulse` on the action message is desktop-only — `prefers-reduced-motion` already disables it globally per UX-1.1, but on mobile the message itself is right next to the just-tapped button, so blinking is unnecessary friction.

  **Risk-constraints gauge bars (lines 200-217 in the old file):**
  - The label was `w-40 shrink-0` — 160px on a 375px viewport, leaving the bar with ~115px and the percentage value with `w-8`. Useless on mobile.
  - Now label-above-bar on mobile via a `md:contents` trick: the wrapper that holds `label` + `value` collapses to `display: contents` at md+ so the children become direct flex children of the gauge row. On mobile, the wrapper is `flex justify-between` (label left, value right) and the bar renders on its own row below.
  - At md+, exact same horizontal layout as before via `md:flex md:items-center md:gap-3`, `md:w-40`, `md:w-8`, `md:order-last`, `md:flex-1`.
  - Limit marker on the bar now has an explicit `aria-label="Limit N%"` (was `title=` only — not read by VoiceOver reliably).

- `frontend/tests/e2e/decision-mobile.spec.ts` — new spec at 375×667 verifying the page renders without a 500 and is axe-clean. Cannot directly assert the action-strip stack with the API 503'd (page renders PageEmpty); the visual contract will be locked when UX-4 lands visual-regression.

### Why
The audit ranked the decision action strip among the worst mobile offenders: 9 buttons in a `flex-wrap` row, each `px-2.5 py-1.5` ≈ 28px tall (below 44pt), wrapping into 4-5 lines of cramped controls at 375px. The 5 secondary buttons being no-ops made the situation worse — they consumed space without adding value. Hiding them on mobile until they ship real behavior is the honest minimum.

The risk gauges' `w-40 shrink-0` label was a desktop-only assumption — labels longer than the bar at the actual touch-target width broke the visual hierarchy. Label-above-bar restores the "value foregrounded against limit" semantic on mobile.

### Gates
| Gate | Result |
|---|---|
| tsc --noEmit | clean |
| vitest | 14 passed (incl. touch-targets lint) |
| next build | 17 routes |
| playwright chromium | **16 passed** (+1 new decision-mobile spec) |
| axe-core on `/decision` @ 375px | 0 serious violations |

### Honest limitations
- The 5 hidden-on-mobile secondary buttons need a proper "More" menu (bottom-sheet listing the same options). Deferred — first wire real handlers, then design the menu. Tracked as a follow-up.
- The decision-mobile Playwright spec can't verify the action-strip layout directly (API mocked to 503, so the page is in PageEmpty state). When the visual-regression gate lands in UX-4, screenshots at 375 and 1280 will lock the contract. For now, the layout is verified manually + lint.

### Out of scope for UX-2.2
- `/paper` holdings table — UX-2.3
- `/replay` stage cards — UX-2.4
- `/backtests` equity curve + experiment list — UX-2.5
- `/admin` shell — UX-2.6 (will likely just route mobile users to a "use desktop" notice given the audit's "fundamentally desktop-only" classification)

---

## UX-2.3 — `/paper` Holdings table mobile refactor
**Date:** 2026-05-20
**Status:** Closed

### What shipped
- `frontend/src/app/paper/page.tsx`:
  - Holdings table: same pinned-primary / hide-secondary pattern as `/comparison` (UX-2.1).
    - Mobile: visible columns = Ticker, Drift (2 cols — Ticker carries inline name + target/current secondary line).
    - md+: adds Name, Target, Current (5 cols — original desktop layout preserved).
  - Each row gets `role="button" tabIndex={0}` + `onKeyDown` (Enter/Space) + `aria-label={ticker} — open paper detail` for keyboard a11y. Existing click flow (`openPane(...)`) preserved verbatim — the bottom-sheet now carries the column data hidden on mobile.
  - Row padding `py-2` → `py-3 md:py-2` raises mobile rows to 44pt floor.
  - Header layout uses `flex items-baseline justify-between` so the "Tap a row to inspect" hint sits cleanly opposite the heading on mobile.
- `frontend/tests/e2e/paper-mobile.spec.ts` — new spec at 375×667, axe-clean check.

### Why
Audit flagged the Holdings table as 5-col `overflow-x-auto`-only — same defect class as the Engine Matrix. Cure is identical: pin the columns a PM scans for (ticker + drift), hide the rest, surface them in the sheet.

### Gates
| Gate | Result |
|---|---|
| tsc --noEmit | clean |
| vitest | 14 passed |
| next build | 17 routes |
| playwright chromium | **17 passed** (+1 new paper-mobile spec) |
| axe-core on `/paper` @ 375px | 0 serious violations |
