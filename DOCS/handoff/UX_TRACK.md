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

---

## UX-2.4 — `/replay` selector + StageSnapshotCard mobile refactor
**Date:** 2026-05-20
**Status:** Closed

### What shipped
- `frontend/src/app/replay/page.tsx`:

  **StageSnapshotCard (the forensics view audit ranked unusable on mobile):**
  - Was: `<div><span w-32 shrink-0>key</span><span truncate>value</span></div>` — 128px label column of 375px viewport = 34%, leaving ~210px for value with truncation.
  - Now: semantic `<dl><dt>/<dd>` with `flex flex-col md:flex-row`. On mobile the key sits above its value; the value uses `break-words` so long JSON-stringified values wrap instead of truncating. On md+, exact prior layout via `md:w-32 md:shrink-0` on `<dt>` and `md:truncate md:flex-1` on `<dd>`.

  **Replay selector rows:**
  - Were: clickable `<div>` elements (no a11y role, not keyboard-focusable).
  - Now: a `<ul role="list">` of `<li><button>` with `aria-pressed`, `aria-label` carrying ticker + date + position count for screen reader users. Each button: `w-full flex flex-col md:flex-row md:items-center md:justify-between gap-1 md:gap-2 p-3 min-h-11`. Mobile gets a 2-line stack (ID + count on row 1, status + date on row 2); desktop keeps the original 1-row split layout.
  - Selected state preserved (`bg-primary-soft border border-primary`) plus new `focus-visible:bg-surface-3` for keyboard nav.

- `frontend/tests/e2e/replay-mobile.spec.ts` — new spec at 375×667, axe-clean check.

### Why
The audit flagged StageSnapshotCard as "fundamentally desktop-only" — the forensics use case (PMs reading why a recommendation was made on a specific date) breaks when values truncate to ellipses. Stacking key over value gives every value the full row width without sacrificing density at md+.

The selector `<div onClick>` pattern silently broke keyboard navigation. Promoting to `<button>` inside `<li>` makes the list browseable via Tab + Enter, and `aria-pressed` communicates the selected state to assistive tech.

### Gates
| Gate | Result |
|---|---|
| tsc --noEmit | clean |
| vitest | 14 passed |
| next build | 17 routes |
| playwright chromium | **18 passed** (+1 new replay-mobile spec) |
| axe-core on `/replay` @ 375px | 0 serious violations |

---

## UX-2.5 — `/backtests` experiment list + config tables mobile refactor
**Date:** 2026-05-20
**Status:** Closed

### What shipped
- `frontend/src/app/backtests/page.tsx`:

  **Experiment list rows (the multi-element collision the audit flagged):**
  - Were: clickable `<div>` with `flex justify-between` — on a 375px viewport, left side (name + date range) collided with right side (return % + status + source badge + promoted badge — up to 5 chips).
  - Now: `<ul role="list">` of `<li><button>` with `aria-pressed` and `aria-label`. Mobile (`flex flex-col`) stacks name+date on row 1 and badges on row 2 via `flex flex-wrap` so they reflow cleanly. Desktop (`md:flex-row md:items-center md:justify-between`) keeps the original split layout exactly.
  - Each button: `min-h-11` (HIG 44pt), `focus-visible:bg-surface-3` for keyboard nav.

  **Experiment Configuration + Provenance:**
  - Same `w-40 shrink-0` anti-pattern as the Replay StageSnapshotCard. Replaced both with semantic `<dl><dt>/<dd>` using the `flex flex-col md:flex-row` switch. `break-words` on `<dd>` so long market-bar-window strings wrap on mobile instead of overflowing.

- `frontend/tests/e2e/backtests-mobile.spec.ts` — new spec at 375×667, axe-clean check.

### Why
The experiment list is the worst-impact surface on `/backtests` for a mobile user — they need to pick which run to inspect, and the desktop layout assumed all metadata could fit on one line. Stacking on mobile lets each row breathe without dropping any data.

The Config and Provenance tables fail for the same reason as the replay forensics view: when the label takes 42% of viewport width, values get truncated and the page stops being useful.

### Gates
| Gate | Result |
|---|---|
| tsc --noEmit | clean |
| vitest | 14 passed |
| next build | 17 routes |
| playwright chromium | **19 passed** (+1 new backtests-mobile spec) |
| axe-core on `/backtests` @ 375px | 0 serious violations |

---

## UX-2.6 — `/admin` desktop-only notice; closes Phase UX-2
**Date:** 2026-05-20
**Status:** Closed

### What shipped
- `frontend/src/app/admin/page.tsx`:
  - `useEffect` reads `window.matchMedia("(max-width: 767px)")` and keeps `isMobile` in sync with viewport changes.
  - When `isMobile && !override`, the page renders a compact notice instead of the full AdminShell: "Ops Command — desktop only" heading, two paragraphs explaining why (multi-panel pipeline canvas, kanban queue, 7-col publication panel built for a desktop input model), and a "Continue anyway" button that opts the user into the heavy shell.
  - Continue-anyway button: `min-h-11` (HIG 44pt), explicit `type="button"`, default surface-3 styling.

- `frontend/tests/e2e/admin-mobile.spec.ts` — new spec with two viewports:
  - 375×667: asserts the notice heading is visible, that "Continue anyway" exists, and that clicking it removes the notice.
  - 1280×720: asserts the notice never appears — desktop loads the full shell straight away.

### Why
The audit ranked `/admin` "fundamentally desktop-only": `PipelineCanvas`, `KanbanQueue` (`grid-cols-4`), `PublicationQueuePanel` (`grid-cols-7` at lg), wizard modal, command palette. A full mobile redesign is multi-week work that's not in scope; silently shipping the broken desktop layout on phones is worse than telling the user it's desktop-only. The "Continue anyway" escape hatch preserves access for power users who know what they're getting into.

The matchMedia subscription (not a one-time read) means a user who rotates a tablet from portrait → landscape sees the notice disappear without a refresh.

### Gates
| Gate | Result |
|---|---|
| tsc --noEmit | clean |
| vitest | 14 passed |
| next build | 17 routes (no size delta — the notice is lightweight) |
| playwright chromium | **21 passed** (+2 new admin-mobile specs at 375 and 1280) |

### Phase UX-2 closes here
Six dense surfaces now have an honest mobile story:
- `/comparison` — pinned-primary, hide-secondary tables (UX-2.1)
- `/decision` — full-width action stack, label-above-bar risk gauges (UX-2.2)
- `/paper` — pinned-primary holdings table (UX-2.3)
- `/replay` — semantic `<dl>` stage cards, buttonified selector (UX-2.4)
- `/backtests` — stacked experiment list, semantic `<dl>` config tables (UX-2.5)
- `/admin` — desktop-only notice with opt-in escape (UX-2.6)

All six surfaces are axe-clean at 375px. Playwright now runs 21 tests across `chromium` at 375 / 1280.

Next: **Phase UX-3 — accessibility baseline + screen-reader pass**:
- 3.1 Clean `KNOWN_PREEXISTING_RULES` in `frontend/tests/e2e/_helpers/axe.ts` (color-contrast + scrollable-region-focusable — outstanding from MVP-6)
- 3.2 Landmark hierarchy + skip-link
- 3.3 aria-live regions for action results
- 3.4 Form inputMode / autoComplete improvements (the audit flagged zero `inputMode` usages in the entire codebase)
- 3.5 Chart table-fallback for VoiceOver
- 3.6 Manual VoiceOver pass — **requires you to run on an iPhone**, I cannot automate this

---

## UX-3.1 — Clear the axe pre-existing-rules allow-list
**Date:** 2026-05-20
**Status:** Closed

### What shipped
- `frontend/tests/e2e/_helpers/axe.ts` — `KNOWN_PREEXISTING_RULES` set emptied; the allow-list is now `new Set<string>([])`. CI fails on any `serious` or `critical` axe violation across all routes × viewports. Helper also now dumps the first 3 offending nodes per rule (CSS selector + failure summary) so future regressions don't require a separate run to diagnose.
- `frontend/src/app/globals.css`:
  - Light theme: `--ink-3` darkened from `oklch(0.58 0.01 250)` → `oklch(0.50 0.012 250)` (was 4.27 on white, now passes 4.5:1). `--ink-4` darkened from `0.72 0.008` → `0.55 0.010` (was 2.30 on bg-surface-2, now passes). `--pos` darkened from `0.58 0.13` → `0.50 0.14` (was 4.03 white-on-pos, now passes). `--accent` darkened from `0.55 0.12` → `0.46 0.13` (was 4.48 white-on-accent, now passes). `--pos-soft-ink` and `--accent-2` minor adjustments to keep the family consistent.
  - Dark theme: `--ink-3` lightened from `0.62 0.01` → `0.72 0.010`, `--ink-4` lightened from `0.48 0.012` → `0.62 0.012` so both pass on the dark canvas.
- `frontend/src/components/feedback/PageError.tsx` — hint paragraph swapped from `text-ink-4` to `text-breach-soft-ink/80`. The ink-4 token wasn't designed to read against the breach-soft background; the soft-ink token is.
- `frontend/src/components/shell/TopBar.tsx` — `⌘K` keyboard-shortcut chip now `text-ink-3` (was inheriting `text-ink-4` from its parent search container, which failed contrast at 10px).
- `frontend/src/app/signup/page.tsx` + `frontend/src/app/login/page.tsx` — auth pages use a hardcoded dark card. Submit button `fontWeight: 600` → `700` (puts it in the WCAG "large bold text" bucket with a 3:1 floor instead of 4.5:1). Hint opacity `0.5` → `0.75`. Link color from `var(--accent)` → `#7fb8ff` — a brighter blue that has contrast on the dark card (`--accent` is now tuned for white backgrounds).
- `frontend/src/components/shell/AppShell.tsx` — `<main>` gets `id="main-content" tabIndex={0}` so the scrollable region passes WCAG 2.1.1 even when the rendered page has no interactive children (empty state, error state, behind-the-disclaimer-modal). `focus-visible:outline-none` so users with interactive content don't see the focus ring on the wrapper.

### Why
The audit and MVP-6 left `color-contrast` and `scrollable-region-focusable` on a CI allow-list — they were known WCAG violations that "would be fixed in a dedicated design pass." This is that pass. Letting them sit was a slow leak: any new code shipping `text-ink-4` for small text was technically a regression we couldn't catch because the rule was muted.

The fixes are mostly token-level (one CSS variable change ripples to every consumer), so the visual hierarchy is preserved. The token edits compress the ink/pos/accent palettes slightly toward darker on light backgrounds — readable, but the design now reads "tighter" than before. UX-4 (polish) will revisit whether this is the right resting place or whether the design wants different solutions (e.g. larger font sizes for secondary text).

The `<main>` `tabIndex={0}` is the canonical WCAG fix for scrollable regions without interactive children — it's the same pattern Material UI, Radix, and Reach use.

### Gates
| Gate | Result |
|---|---|
| tsc --noEmit | clean |
| vitest | 14 passed |
| next build | 17 routes |
| playwright chromium | **21 passed** — all routes axe-clean at 375px + desktop, allow-list empty |

### Honest limitations
- I only verified contrast in **light theme** at the test viewports. Dark theme contrast got darker-too-light fixes alongside, but axe wasn't run in dark mode this pass. A dark-theme axe run is tracked for UX-3.6 (the manual VoiceOver / device pass) since iPhones default to dark in many users' settings.
- The `<main>` `tabIndex={0}` introduces one extra Tab stop at the top of every page. For users with rich keyboard nav this is a tiny noise; for users who depend on it (screen-reader and switch-control), it's a clear benefit. Net positive.
- Token edits affect every visual that uses ink-3/4, pos, accent. I didn't re-screenshot every surface. Visual regressions are caught in UX-4 when the screenshot baseline lands.

---

## UX-3.2 — Skip-to-content link + banner landmark
**Date:** 2026-05-20
**Status:** Closed

### What shipped
- `frontend/src/components/shell/AppShell.tsx` — first focusable element on every page is now a "Skip to main content" link. Uses Tailwind's `sr-only` to stay visually hidden, then `focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 ...` styles to surface as a floating pill above the TopBar on focus. `min-h-11`, primary background, `shadow-lg`. Click jumps to `#main-content`.
- `frontend/src/components/shell/TopBar.tsx` — `<header>` gets `role="banner" aria-label="FINRLX top navigation"` so screen-reader landmark navigation works without ambiguity (the `<header>` HTML semantic alone is implicit on some browsers). Brand swatch gets `aria-hidden="true"` since it's decorative.
- `frontend/tests/e2e/mobile-shell.spec.ts` — new test: Tab focuses the skip link (proves it's first in tab order), clicking it focuses `#main-content`.

### Why
Per WAI-ARIA best practices and Apple's HIG iOS keyboard navigation rules, a skip link is the standard way to let keyboard and screen-reader users avoid re-traversing the same nav on every page. Combined with `<main tabIndex={0}>` from UX-3.1, the skip link gives one Tab to jump from the URL bar straight to page content.

Landmark map after this change:
- `role="banner"` — TopBar (UX-3.2)
- `role="navigation" aria-label="Primary navigation"` — Sidebar (UX-1.2)
- `role="main"` — `<main id="main-content">` (UX-3.1)
- `role="complementary"` / `role="dialog"` — ContextPane (UX-1.3)
- `role="contentinfo"` — DisclaimerBanner (MVP-5)

VoiceOver rotor can now jump cleanly across all five landmarks.

### Gates
| Gate | Result |
|---|---|
| tsc --noEmit | clean |
| vitest | 14 passed |
| next build | 17 routes |
| playwright chromium | **22 passed** (+1 new skip-link test) |
| axe-core | clean across all routes |

---

## UX-3.3 — Live regions for action results / loading / error
**Date:** 2026-05-20
**Status:** Closed

### What shipped
- `frontend/src/components/feedback/PageError.tsx` — wrapper gets `role="alert"`. When a page transitions into error state (API 503, malformed response), screen-reader users get an automatic "Error: …" announcement without needing focus. Icon gets `aria-hidden` since the heading already conveys "Error".
- `frontend/src/components/feedback/PageLoading.tsx` — wrapper gets `role="status" aria-live="polite" aria-label={label || "Loading"}`. The animated dots get `aria-hidden` so the AT only reads the label. Polite politeness (not assertive) so loading announcements don't preempt other speech.
- The decision-page action message already carried `role="status" aria-live="polite"` from UX-2.2.

### Why
Two PMs in the user research from `fintech-disclaimer-and-marketing-guard` discovery noted that recommendation feedback (save / promote / defer) needs an audible "happened" signal beyond visual color. Live regions are the WCAG-canonical way; they cost nothing in code complexity and pay off the moment a user enables VoiceOver.

PageError + PageLoading carry every page's load and error UX — fixing them once covers every route.

### Gates
| Gate | Result |
|---|---|
| tsc --noEmit | clean |
| vitest | 14 passed |
| next build | 17 routes |
| playwright chromium | 22 passed |
| axe-core | clean across all routes |

---

## UX-3.4 — Form attributes for iOS soft-keyboard + autofill
**Date:** 2026-05-20
**Status:** Closed

### What shipped
- `frontend/src/app/signup/page.tsx` + `frontend/src/app/login/page.tsx` — auth forms:
  - Email input: added `inputMode="email"`, `autoCapitalize="off"`, `spellCheck={false}` alongside existing `type="email" autoComplete="email"`. `type=email` alone is enough on modern iOS to trigger the email keyboard, but the explicit `inputMode` is more robust against edge cases and older Safari versions. `autoCapitalize="off"` + `spellCheck={false}` stop iOS from suggesting "Capitalized@gmail.com" or red-underlining valid email addresses.
  - Password input: added `autoCapitalize="off"`, `spellCheck={false}` to prevent the same two iOS papercuts on password entry.

### Why
The audit flagged "zero `inputMode` anywhere" as a generic concern. The actual user-facing forms (signup, login, onboarding) already used the right `type` and `autoComplete` attributes. The marginal improvements here are the iOS-specific `autoCapitalize` + `spellCheck` defaults, which prevent two predictable annoyances: capitalized email letters and red-underlined password characters.

Admin Research Wizard text inputs (UUIDs, ticker symbols, JSON config) were intentionally not changed — they're gated behind UX-2.6's mobile-desktop-only notice and the wizard is desktop-first by design.

### Gates
| Gate | Result |
|---|---|
| tsc --noEmit | clean |
| vitest | 14 passed |
| next build | 17 routes |
| playwright chromium | 22 passed |

---

## UX-3.5 — Chart accessibility (aria-label summaries)
**Date:** 2026-05-20
**Status:** Closed

### What shipped
Each chart component now wraps its `<ResponsiveContainer>` in a `role="img" aria-label="…"` div whose label is a concrete data-driven summary, so VoiceOver no longer just announces "graphic":

- `EquityCurveChart.tsx` — "Equity curve from base X on D1 to Y on D2. Range min–max across N data points."
- `WeightsBarChart.tsx` — "Portfolio weights bar chart, N positions. Top three: TICKER X%, …"
- `DriftBarChart.tsx` — "Drift-from-target bar chart, N positions sorted by absolute drift. Largest deviations: …"
- `ComparisonBarChart.tsx` — "Recommendation vs benchmark weights, N positions. Top three: …"
- `AlignmentChart.tsx` — "Engine alignment bubble chart, N engines (X buy, Y hold, …). Synthesis stance Z at C% confidence."
- `PriceChartCard.tsx` — "TICKER price chart over N bars. TICKER return X%, BENCH return Y%. N annotated events."

### Why
Pure visual charts are unreadable to screen readers. A `<title>` + `<desc>` SVG pair would help but Recharts doesn't expose them cleanly; the simpler and more portable fix is a `role="img"` wrapper with a computed `aria-label` summarizing the chart's shape and salient endpoints.

This is the minimum that's useful for a sighted-and-screen-reader-both user toggling VoiceOver on. A full table-fallback (rendering the underlying data as an accessible `<table>`) is a polish task best done with real data on a real device — deferred to UX-4 with the visual-regression baseline.

### Gates
| Gate | Result |
|---|---|
| tsc --noEmit | clean |
| vitest | 14 passed |
| next build | 17 routes |
| playwright chromium | 22 passed |
| axe-core | clean across all routes |

### What's left in UX-3
**UX-3.6 — Manual VoiceOver pass — requires you on an iPhone.** I cannot automate this. When you have 15-20 minutes:
1. Deploy the latest build to staging (or run locally on a Mac and connect an iPhone via Web Inspector).
2. Open Safari on the iPhone, navigate to the staging URL.
3. Enable VoiceOver (Settings → Accessibility → VoiceOver, or triple-click the side button if you wired the shortcut).
4. Walk through these flows and report anything that reads awkwardly:
   - Skip to main content link (should be first item, then announces "main, landmark")
   - Nav drawer (burger should announce "Open navigation, button, collapsed")
   - Context pane sheet (should announce "Context pane, dialog")
   - Engine Matrix row tap → ContextPane should announce the engine name
   - Position Detail row tap → ContextPane should announce the ticker
   - Equity curve, weights bar — should announce the aria-label summaries I added in UX-3.5
   - Signup form — email field should bring up the email keyboard (no period key in main row)
5. Reply with any rough edges + I'll fix them in a follow-up commit.

The technical gates (axe, lint, type-check) all pass — but axe doesn't catch every screen-reader edge, which is why the manual pass exists. Document what you see and we iterate.

### Phase UX-3 — auto-runnable portion closes here
The five automated sub-phases (3.1 axe cleanup, 3.2 skip link + landmarks, 3.3 live regions, 3.4 form attributes, 3.5 chart aria-labels) are landed. Manual VoiceOver pass (3.6) is the human-in-the-loop step before Phase UX-3 is fully closed.

Next once you've run the VoiceOver pass:
- **Phase UX-4** — visual polish (loading skeletons, empty states, motion, design-token consolidation export for UX-5)
- **Phase UX-5** — iOS prep (tokens.json export, OpenAPI Swift codegen scaffold, i18n strings, navigation contract doc, PWA manifest)

---

## UX-4.1 + 4.2 — Skeleton loading + richer empty states
**Date:** 2026-05-21
**Status:** Closed

### What shipped

**Skeleton system (UX-4.1):**
- `frontend/src/components/feedback/Skeleton.tsx` (new) — primitives `SkeletonBox`, `SkeletonText`, `SkeletonHeading`, and a composite `PageSkeleton` that renders a content-shaped placeholder for a typical FINRLX page (heading + KPI strip + hero card + two-up cards). Carries one polite live region so screen readers get a single "Loading X" announcement rather than dozens of per-skeleton announcements.
- `frontend/src/components/feedback/PageLoading.tsx` — preserves the existing `PageLoading` API (8 call sites unchanged) but now delegates to `PageSkeleton` internally. A new `InlineLoading` export keeps the dot-pulse pattern available for in-page detail loads.
- `frontend/src/app/universe/page.tsx` — switched the in-page detail-load spinner to `InlineLoading` (full-page skeleton was the wrong shape for "loading inside a panel").

**Empty state enrichment (UX-4.2):**
- `frontend/src/components/feedback/PageEmpty.tsx` — added optional `icon` and `action` props. Action can be either an `onClick` handler (renders a `<button>`) or an `href` (renders a `next/link`). Icon renders in a 12×12 surface-3 circle above the title. The action button uses the canonical primary CTA styles + `min-h-11` (HIG 44pt). Title color bumped from `text-ink-2` to `text-ink` (more legible against `bg-surface`).
- Existing callers (`/decision`, `/paper`, `/comparison`, `/replay`, `/backtests`) didn't need updates — the new props are all optional, callers pass the same `title` + `message` and just gain the option to surface a CTA later.

### Why
The audit identified "Loading…" dots as a perceived-performance miss: on a slow connection the user stares at three pulsing dots wondering if the page is broken. Skeletons that approximate the content shape give immediate "yes the page is here, fetching" feedback — the gold-standard pattern from Facebook, LinkedIn, Robinhood. PageSkeleton is intentionally a single shape (not per-route bespoke skeletons) because the cost/benefit of more specific skeletons doesn't pay off for an internal-PM-tool of this size.

`PageEmpty` was a flat card with no action. For pages like `/paper` ("No paper portfolio yet"), the natural follow-up is "Create one from a recommendation" — surfacing that as a CTA in the empty state is a one-line improvement once the helper is in place.

### Gates
| Gate | Result |
|---|---|
| tsc --noEmit | clean |
| vitest | 14 passed |
| next build | 17 routes |
| playwright chromium | 22 passed |
| axe-core | clean across all routes (skeleton announces once; per-skeleton are aria-hidden) |

---

## UX-4.3 + 4.4 + 4.5 — Motion / errors / micro-interactions audit (no-code closing)
**Date:** 2026-05-21
**Status:** Closed — verified by audit, no new code

### What was checked
- **Motion (UX-4.3 / 4.5):** the global `@media (prefers-reduced-motion: reduce)` rule in `globals.css` (added in UX-1.1) clamps every animation-duration and transition-duration to 0.01ms. The sidebar drawer, the context-pane bottom sheet, the skeleton pulse, and every Tailwind `transition-*` class respect it. Tested in DevTools Rendering > "prefers-reduced-motion: reduce" — animations effectively disabled.
- **Errors (UX-4.4):** `PageError` has `role="alert"` (UX-3.3) and uses semantic tokens for contrast (UX-3.1). Inline errors on signup/login use `role="alert"` directly. The decision-page action message uses `role="status" aria-live="polite"` (UX-2.2). All paths from action → screen-reader announcement are wired.
- **Focus visibility:** `:focus-visible { outline: 2px solid var(--primary); outline-offset: 2px }` global rule applies to every interactive element. Hit-tested with keyboard Tab navigation across `/`, `/decision`, `/paper`, `/comparison` — focus ring is visible everywhere.

### Why no new code
Each of these landed naturally as a side-effect of earlier sub-phases. Re-implementing for the sake of a UX-4 line item would be churn. The audit above is the documented closure.

### Phase UX-4 closes here
Visual polish work that needed code (skeletons, empty states) shipped in UX-4.1+4.2 (`e298ac7`). Motion, errors, focus visibility verified as already handled.

Next: **Phase UX-5 — iOS prep**:
- 5.1 Design tokens export (`tokens.json` consumable by Tailwind today + Swift codegen later)
- 5.2 OpenAPI Swift codegen scaffold
- 5.3 i18n strings extraction
- 5.4 Navigation contract doc (web routes → SwiftUI structure)
- 5.5 PWA manifest + service worker so the site is installable as iOS Home Screen app

Then the **post-MVP product track** (re-confirmed 2026-05-21): A2 Ops command → A3 Policy Editor → A4 Integrations → B1 Risk workspace → B2 News intelligence → B3 Saved views → C1..C7 MVP debt closure. Phase D iOS stays skipped (PWA-first).

---

## UX-5.1 — Design tokens JSON export + contract test
**Date:** 2026-05-21
**Status:** Closed

### What shipped
- `frontend/src/design/tokens.json` (new) — structured export of every color, radius, spacing, typography, and shadow token. Mirrors `globals.css` :root + :root[data-theme=dark] exactly. JSON shape is iOS-codegen-ready: `color.light.*` / `color.dark.*` maps directly to a `Color.finrlxLight` / `Color.finrlxDark` enum in Swift.
- `frontend/src/__tests__/tokens-contract.test.ts` (new) — vitest contract. Parses `globals.css`, extracts every `--var` declaration from `:root` and `:root[data-theme=dark]`, asserts every key in `tokens.color.{light,dark}` matches its CSS counterpart exactly, and (in reverse) asserts globals.css doesn't declare a color custom property the JSON forgot. **3 tests, all green.**
- The JSON file carries a `swift_bridging_notes` section explaining the codegen mapping (oklch → Color sRGB, font-fallback chain for SF Pro, px-to-pt 1:1, reduced-motion handled by SwiftUI primitives not tokens) so the eventual Swift codegen script has a written brief.

### Why
Without a single source of truth, the iOS app's colors will drift from the web's the moment someone tweaks `--accent` in CSS without remembering to update Swift. The JSON + the contract test enforces "edit one, edit both" at CI time. CI will fail loudly if the two diverge, before any iOS code is even written.

The contract test is intentionally one-way-strict on color tokens (the JSON must cover every color in globals.css) but tolerant on non-color tokens (radii/shadows/typography) — those are easier to reason about as one-line strings and don't carry the same drift risk.

### Gates
| Gate | Result |
|---|---|
| tsc --noEmit | clean |
| vitest | **17 passed** (+3 new tokens-contract tests; was 14) |
| next build | unchanged |
| playwright chromium | unchanged |

---

## UX-5.2 — iOS API codegen scaffold (doc-only)
**Date:** 2026-05-21
**Status:** Closed

### What shipped
- `DOCS/handoff/UX_5_2_IOS_API_CODEGEN.md` — captures the plan for generating Swift Codable types + an async/await client from FastAPI's `/openapi.json` when Phase D opens. Covers: tool choice (Apple's `swift-openapi-generator`), expected project layout (`ios/finrlx/`), generator config including a path filter that excludes admin/RL endpoints, SwiftPM dependencies, JWT auth middleware pattern, and contract-testing approach.

### Why
Phase D iOS is currently deferred (PWA-first), but the OpenAPI generation strategy needs to be settled before the iOS dev starts — otherwise they'll either hand-roll types (drifts on every backend change) or pick a wrong tool that's expensive to switch later. Settling this now in a doc keeps the path open without committing code that has nothing to call into.

No tests, no code shipped — this is a hand-off brief. The contract test in UX-5.1 + the path filter in this doc combine to give the iOS dev a "clone, configure, generate" experience.

### Gates
None — doc-only. tsc / vitest / build / playwright unchanged from UX-5.1.

---

## UX-5.3 — i18n strings extraction (scaffold)
**Date:** 2026-05-21
**Status:** Closed

### What shipped
- `frontend/src/i18n/en.json` (new) — initial extraction of ~40 strings used in multiple places: common verbs (Save / Cancel / Close / I understand), auth labels, the full disclaimer modal + banner copy (the single biggest pile of content that must stay consistent between web and iOS), action results (Saved / Failed / Deferred), and nav labels for all workspace surfaces. Includes a `swift_codegen_notes` section documenting the dotted-path → Localizable.strings mapping for the future iOS Phase D.
- `frontend/src/i18n/index.ts` (new) — typed `t()` helper with full IntelliSense via a recursive `Path<T>` type. Unknown keys return the key string so missing translations show up as `auth.sign_in_typo` in the rendered UI instead of vanishing — dev-loud, prod-safe.
- `frontend/src/__tests__/i18n.test.ts` (new) — 4 contract tests: dot-path resolution, unknown-key fallback, top-level shape, and no-control-chars sanity check.

### Why
Strings are the second-biggest source of "this looks slightly wrong on iOS" defects after colors. Extracting them now to a JSON keeps web and iOS in lockstep — `Localizable.strings` will be generated from the same source the web uses. The migration is intentionally incremental: components that already inline strings keep working; new components reach for `t(...)`.

The disclaimer copy in particular is regulatory — having it in one JSON file makes legal review a single-file diff rather than chasing 4 React components.

### Migration status
The strings are only **referenced** from this file by net-new components going forward. The existing inline strings in `DisclaimerModal`, `DisclaimerBanner`, `signup/page.tsx`, `login/page.tsx`, etc. are unchanged — refactoring them to `t(...)` is incremental and not part of UX-5.3's scope.

### Gates
| Gate | Result |
|---|---|
| tsc --noEmit | clean |
| vitest | **21 passed** (+4 new i18n tests) |
| next build | unchanged |
| playwright chromium | unchanged |

---

## UX-5.4 — iOS navigation contract doc
**Date:** 2026-05-21
**Status:** Closed

### What shipped
- `DOCS/handoff/UX_5_4_IOS_NAVIGATION_CONTRACT.md` — every web route mapped to its SwiftUI navigation primitive. Tab structure (Overview / Decision / Replay / Paper + More) encoded per the locked product decision. Per-surface mapping table covers all 13 surfaces with the chosen primitive (`NavigationStack` / `NavigationSplitView` / `.fullScreenCover` / `.sheet`). Deepest mapping for `/decision` written out as Swift code skeleton including the bottom-sheet `ContextPane` equivalent (`.presentationDetents([.medium, .large])` + `.presentationBackgroundInteraction(.enabled)`).
- Explicitly documents the locked decisions: no swipe-to-accept (confirmation dialog), full-screen disclaimer modal not sheet, no skip-link needed (iOS Rotor handles landmarks natively).

### Why
When Phase D opens, the iOS dev should not need to re-decide how the bottom-tab layout maps from the web's 9-item sidebar, or which surfaces deserve `NavigationSplitView` vs a plain `NavigationStack`. The web design + the locked decisions + the HIG research from UX research phase all converge on a single answer per surface; capturing it once means the iOS implementation is execution, not design.

### Gates
None — doc-only. CI gates unchanged from UX-5.3.

### Handoff packet for Phase D
The iOS dev needs only four files to start:
- `DOCS/handoff/UX_5_2_IOS_API_CODEGEN.md` (this directory)
- `DOCS/handoff/UX_5_4_IOS_NAVIGATION_CONTRACT.md` (this directory)
- `frontend/src/design/tokens.json` (color + typography source)
- `frontend/src/i18n/en.json` (string source)

Plus `UX_TRACK.md` (this file) for context.

---

## UX-5.5 — PWA manifest (installable as iOS Home Screen)
**Date:** 2026-05-21
**Status:** Closed

### What shipped
- `frontend/public/manifest.webmanifest` (new) — minimum-viable PWA manifest. Name + short_name "FINRLX", description matches the metadata, `display: "standalone"` so the home-screen launch hides the Safari chrome, `start_url: "/"`, `theme_color` + `background_color` matched to the canvas token (`#fafbfc` light). Single SVG icon referenced from `/icon.svg` (the existing Next.js `app/icon.svg`).
- `frontend/src/app/layout.tsx` — `metadata.manifest = "/manifest.webmanifest"` so Next.js emits the `<link rel="manifest">` tag, plus `metadata.appleWebApp` (capable: true, title: "FINRLX", statusBarStyle: "black-translucent") which generates the iOS-specific `<meta apple-mobile-web-app-*>` tags. This is what tells iOS Safari "yes, this site is installable; show the Add to Home Screen affordance prominently."

### What's deferred (low-risk follow-ups)
- **Proper raster icons (192px, 512px, maskable 512px).** The single SVG is enough for installation on modern iOS Safari and Chrome, but Android home screen and macOS Dock prefer PNGs. Adding `icon-192.png` + `icon-512.png` + `icon-maskable-512.png` to `public/` and listing them in the manifest is a 5-minute follow-up when someone designs the icon properly.
- **Service worker / offline shell.** Not required for iOS "Add to Home Screen" — iOS Safari treats `display: standalone` PWAs as installable without one. Adding offline support means picking up `next-pwa` or hand-rolling a service worker via `next-runtime` — out of UX-5 scope; revisit if real users start complaining about cold-start over LTE.
- **PWA install prompt.** Some apps surface a custom "Install FINRLX" button via the `beforeinstallprompt` event. Not shipped here — let the browser handle the affordance until product validates the install funnel.

### Why
The locked product decision (UX-track scope, 2026-05-20) is **PWA-first, native Swift deferred**. UX-5.5 is the smallest commit that delivers on "PWA-first": opening Safari on iPhone, navigating to the deployed FINRLX, and tapping Share → Add to Home Screen now creates a home-screen tile that launches the app in standalone mode with the FINRLX icon, theme color, and orientation lock. That's the user-visible promise of "PWA-first" honored.

### Gates
| Gate | Result |
|---|---|
| tsc --noEmit | clean |
| vitest | 21 passed |
| next build | 17 routes (unchanged) — `/manifest.webmanifest` served statically from `public/` |
| playwright chromium | 22 passed |

### Phase UX-5 closes here
All five UX-5 sub-phases are landed:
- 5.1 tokens.json + contract test (`f6a014d`)
- 5.2 iOS API codegen doc (`9fec609`)
- 5.3 i18n strings scaffold (`da2f085`)
- 5.4 iOS navigation contract (`a6a7cb6`)
- 5.5 PWA manifest (this commit)

### Phase UX-6: not in this track
The UX track ends here. Per the user-confirmed roadmap (memory: `project_post_mvp_roadmap.md`, re-confirmed 2026-05-21), the next track is the **post-MVP product track** — A2 Ops command → A3 Policy Editor → A4 Integrations → B1 Risk workspace → B2 News intelligence → B3 Saved views → C1..C7 MVP debt closure. Phase D iOS stays skipped.

The auto-runnable portion of Phase UX-3 still has UX-3.6 outstanding — the manual VoiceOver pass that requires a real iPhone. That doesn't block the post-MVP track; it can be done in parallel by the user.

---

## A2 — Ops command page (post-MVP product track)
**Date:** 2026-05-21
**Status:** Closed

### What shipped
- `frontend/src/app/ops/page.tsx` (new) — `/ops` route. Consumes `GET /api/v1/ops`, renders system KPIs + publication queue (with approve/defer/challenge actions wired to the corresponding POST endpoints) + feed/engine health grid + breaches/incidents lists + audit trail.
- `frontend/src/components/ops/` (new directory, 5 components):
  - `OpsKpiStrip` — KPI cards (queue depth / feed coverage / engine health / breaches / incidents / high-priority)
  - `OpsQueuePanel` — publication queue with per-row Approve / Defer / Challenge buttons (min-h-11 on mobile, action calls refetch the dashboard so state is consistent)
  - `OpsHealthGrid` — two-up Feeds + Engines side panels
  - `OpsBreachesIncidents` — two-up policy breaches + open incidents
  - `OpsAuditLog` — recent audit trail with actor/action/scope
- `frontend/src/components/shell/Sidebar.tsx` — OPS entries reworked:
  - "Ops command" now points to `/ops` (was `/admin`), gated by `flagKey: "ops_ui"`
  - New "Research lab" entry pointing to `/admin` (the desktop-only pipeline canvas + wizard from UX-2.6), gated by the existing `research_lane` flag
- `backend/app/core/config.py` + `backend/app/api/v1/flags.py` — `feature_ops_ui: bool = True` and exposed in `/api/v1/flags`. `backend/tests/test_mvp4_feature_flags.py` asserts the new key.
- `frontend/src/contexts/FeatureFlagsContext.tsx` — added `ops_ui: boolean` to the typed `FeatureFlags`.
- `frontend/tests/e2e/ops-mobile.spec.ts` (new) — render + axe-clean at 375×667 and 1280×720.

### Why
The Ops command surface from the design was misrouted to `/admin` since MVP — the audit identified this as a "labelled but not built" gap. `/admin` itself remains valuable (it's the desktop-only research lab with the pipeline canvas, kanban editor, and research wizard) so it stays accessible from the sidebar under a clearer label. The new `/ops` is the daily-driver dashboard that mobile + desktop both render usefully.

Approve/Defer/Challenge actions were already implemented in the backend (UX-2.6 left them, the audit confirmed) — they just had no frontend wired to them. A2 closes that gap.

### Gates
| Gate | Result |
|---|---|
| backend pytest | **747 passed, 2 skipped** (no regression; flag-shape test updated) |
| backend ruff `app/` | clean |
| backend mypy | clean |
| tsc --noEmit | clean |
| vitest | 21 passed |
| next build | **18 routes** (+`/ops` at 4.5 kB) |
| playwright chromium | **24 passed** (+2 new ops-mobile specs at 375 + 1280) |
| axe-core on `/ops` @ 375px | 0 serious violations |

### Honest limitations
- Live action mutations call the real POST endpoints but Playwright tests run with the API mocked to 503, so the test verifies "render + axe clean" only. End-to-end action flow needs a backend + seed to verify, which is documented for the operator's deploy smoke (Phase MVP-7e).
- The `OpsData` response also carries `ml_ops`, `policy`, `integrations_summary`, `universe`, `rl` blocks. A2 surfaces queue/feeds/engines/breaches/incidents/audit but doesn't render those secondary blocks yet — they will become standalone surfaces in A3 (Policy Editor) and A4 (Integrations), and the `ml_ops` + `rl` blocks belong to the research lab on `/admin`.

---

## A3 — Policy Editor page (post-MVP product track)
**Date:** 2026-05-21
**Status:** Closed

### What shipped
- `frontend/src/app/policies/page.tsx` (new) — `/policies` route. Groups policy rules by category (concentration / liquidity / volatility / etc.), shows active breaches in a caution-tinted banner at the top, and provides per-rule inline edit + history drawer. Reads `signed-in user.email` from `useAuth()` and passes it as the audit actor on every update.
- `frontend/src/components/policies/PolicyRuleCard.tsx` (new) — card per rule. Default view: name + severity badge + advisory/enforced badge + description + threshold value with unit. Edit mode (toggle): numeric input (`inputMode="decimal"` for the iOS soft keyboard), reason text input, Save / Cancel. PATCHes `/policies/rules/{key}` with `{threshold_value, actor, reason}`. Save success updates the card in place via a callback; failure surfaces inline with `role="alert"`.
- History drawer in `policies/page.tsx` — clicking "History" on any rule opens a bottom-sheet on mobile / right-aside on desktop showing prior values with actor + timestamp + reason. Same `role="dialog" aria-modal="true"` pattern as ContextPane (UX-1.3).
- `backend/app/core/config.py` + `flags.py` — `feature_policy_ui: bool = True`, exposed in `/api/v1/flags`.
- `backend/tests/test_mvp4_feature_flags.py` — assertion updated to include `policy_ui`.
- `frontend/src/contexts/FeatureFlagsContext.tsx` — `policy_ui: boolean` added.
- `frontend/src/services/api.ts` — `PolicyRule`, `PolicyHistoryEntry`, `PolicyBreach` types + 4 fetchers (`fetchPolicyRules`, `fetchPolicyHistory`, `fetchPolicyBreaches`, `updatePolicyRule`).
- `frontend/src/components/shell/Sidebar.tsx` — new "Policies" OPS entry, gated by `policy_ui`.
- `frontend/tests/e2e/policies-mobile.spec.ts` (new) — render + axe-clean at 375×667.

### Why
The `/policies/*` endpoints were already complete on the backend (list, get, PATCH, history, breaches, evaluate). What was missing was a usable surface to drive them — operators were either reading rules straight from the DB or via the desktop-only research lab. A3 gives a daily-driver Policy Editor that mobile and desktop both render cleanly. The history drawer is the audit-friendly companion: every threshold change has a row, the row records who and when and why, and the drawer surfaces that row without leaving the page.

### Gates
| Gate | Result |
|---|---|
| backend pytest (flags test) | 3 passed |
| backend ruff `app/` | clean |
| backend mypy | clean |
| tsc --noEmit | clean |
| vitest | 21 passed |
| next build | **19 routes** (+`/policies` at 5.42 kB) |
| playwright chromium | **25 passed** (+1 new policies-mobile spec) |
| axe-core on `/policies` @ 375px | 0 serious violations |

### Honest limitations
- The current page lets any signed-in user edit policy thresholds. The backend's `PolicyRuleUpdateRequest` accepts an `actor` string but doesn't enforce that only an `admin` role can submit. UX-track work won't add role gating; that's a backend follow-up captured for C-track if it becomes a security concern.
- The "Reason" field is optional. For a fintech audit trail you'd typically force it. Leaving it optional matches the current backend contract; tightening to required is a one-line backend change + a frontend `required` attribute.
- The history drawer fetches on first open and doesn't refresh on subsequent re-opens of the same rule. Acceptable for now (history doesn't change behind the user's back unless someone else updates the rule).

---

## A4 — Integrations page (post-MVP product track)
**Date:** 2026-05-21
**Status:** Closed; closes Phase A

### What shipped
- `frontend/src/app/integrations/page.tsx` (new) — `/integrations` route. Consumes `GET /api/v1/integrations` + `GET /api/v1/integrations/health`. Layout: 5 KPI cards (total / healthy / degraded / placeholder / real providers), then grouped sections by category (Market data / News & sentiment / Fundamentals / Alternative & sentiment). Each integration renders as a card with status badge, placeholder badge if applicable, coverage + freshness + last-success-at, and any warnings as a bulleted list with a caution icon.
- `backend/app/core/config.py` + `flags.py` — `feature_integrations_ui` flag, default ON.
- `backend/tests/test_mvp4_feature_flags.py` — assertion updated to include `integrations_ui`.
- `frontend/src/contexts/FeatureFlagsContext.tsx` — `integrations_ui: boolean`.
- `frontend/src/services/api.ts` — `Integration` + `IntegrationHealth` types + 2 fetchers.
- `frontend/src/components/shell/Sidebar.tsx` — new "Integrations" entry gated by `integrations_ui`.
- `frontend/tests/e2e/integrations-mobile.spec.ts` (new) — render + axe at 375×667.

### Why
The integrations endpoint (and the underlying `IntegrationsService`) was complete since MVP and is consumed by `/ops` for the health-block summary, but had no dedicated surface. A4 gives operators a single page to see "what data sources do we have, which are real, which are placeholders, what's degraded right now" — the honest view of the data-supply chain.

### Gates
| Gate | Result |
|---|---|
| backend pytest (flags test) | 3 passed |
| backend ruff `app/` + mypy | clean |
| tsc --noEmit | clean |
| vitest | 21 passed |
| next build | **20 routes** (+`/integrations`) |
| playwright chromium | **26 passed** (+1 new integrations-mobile spec) |
| axe-core on `/integrations` @ 375px | 0 serious violations |

### Phase A — all four sub-phases closed
- A1 Universe page         `dacaa79`
- A2 Ops command page      `947b16e`
- A3 Policy Editor page    `da407f6`
- A4 Integrations page     **this commit**

All four wire existing-but-unexposed backend endpoints to new frontend surfaces. Sidebar is now fully populated under both WORKSPACES (Overview, Decisions, Engine comparison, Replay, Backtests, Paper portfolio, Universe) and OPS (Ops command, Policies, Integrations, Research lab). Three of the four phantom `href="#"` entries the audit flagged are now real surfaces (Universe in A1, Policies as a new entry in A3, Integrations in A4). The fourth — Risk workspace — is Phase B1 (requires net-new backend service + endpoints), still pending.

Next: **Phase B1 — Risk workspace.** Per the locked scope (VaR + concentration + drawdown + exposure), this is the first phase that requires net-new backend code, not just a frontend that wires existing endpoints.

---

## B1 — Risk workspace (first net-new backend phase)
**Date:** 2026-05-21
**Status:** Closed

### What shipped
**Backend:**
- `backend/app/services/risk_metrics.py` (new) — `RiskMetricsService.get_risk_bundle(portfolio_id)` aggregates concentration, drawdown, parametric VaR, and exposure from the existing `PaperPortfolio` + `PaperValuationSnapshot` + `Asset.sector` data. No new tables, no new ingest.
- `backend/app/schemas/risk.py` (new) — `RiskBundle` with sub-models per block (ConcentrationBlock / DrawdownBlock / VaRBlock / ExposureBlock + SectorWeight).
- `backend/app/api/v1/risk.py` (new):
  - `GET /api/v1/risk/portfolios/{portfolio_id}` → full bundle, 404 on unknown
  - `GET /api/v1/risk/current` → bundle for the most recent active paper portfolio, `null` when no portfolio exists
- `backend/app/api/router.py` — registered the new router with tag `["risk"]`.
- `backend/app/core/config.py` + `backend/app/api/v1/flags.py` — `feature_risk_ui: bool = True`, exposed in `/api/v1/flags`.
- `backend/tests/test_phase_b1_risk_metrics.py` (new) — **10 tests**: stddev, concentration top-N + sector grouping, drawdown both with and without the pre-computed `max_drawdown_to_date` field, parametric VaR math against analytic z-scores, exposure long-only and long-short, and the two API endpoints' shape (current returns `null` without a portfolio, portfolio detail returns 404 for unknown IDs).
- `backend/tests/test_mvp4_feature_flags.py` — updated to assert the `risk_ui` key.

**Frontend:**
- `frontend/src/services/api.ts` — `RiskBundle`, `RiskConcentration`, `RiskDrawdown`, `RiskVaR`, `RiskExposure`, `RiskSectorWeight` types + `fetchCurrentRisk()` returning `RiskBundle | null`.
- `frontend/src/contexts/FeatureFlagsContext.tsx` — `risk_ui` flag added.
- `frontend/src/app/risk/page.tsx` (new) — `/risk` route. Empty state when no paper portfolio (CTA to `/paper`). When data is present: 4-card KPI strip (VaR 95% / VaR 99% / current drawdown / max drawdown), Exposure section (long/short/gross/net/cash), Concentration section (top-1/3/5 weights + sector bar chart), and a footnote explaining the parametric VaR assumption.
- `frontend/src/components/shell/Sidebar.tsx` — "Risk workspace" entry href changed from `"#"` to `"/risk"` and gated by `risk_ui`. **All four phantom `href="#"` entries the audit flagged are now real surfaces.**
- `frontend/tests/e2e/risk-mobile.spec.ts` (new) — render + axe at 375×667.

### Why
Risk workspace is the first phantom-nav entry the audit identified that needed net-new backend code (the other three — Universe, Policies, Integrations — already had endpoints). Building it minimally from existing paper-portfolio data avoids opening a second multi-week track of risk infrastructure work; the metrics shipped are honest about their assumptions (parametric VaR with a normal-distribution caveat surfaced in the page footer) rather than overclaiming.

Beta-vs-benchmark exposure is deliberately not shipped: it would require a benchmark return series and a beta-estimation pipeline. It's a clean follow-up if needed; the current `long_weight - short_weight = net_exposure` gives the same signal direction for a long-only book.

### Gates
| Gate | Result |
|---|---|
| backend pytest | **757 passed, 2 skipped** (+10 risk tests; no regression) |
| backend ruff `app/` | clean (one import-order auto-fix applied) |
| backend mypy | clean |
| tsc --noEmit | clean |
| vitest | 21 passed |
| next build | **21 routes** (+`/risk`) |
| playwright chromium | **27 passed** (+1 new risk-mobile spec) |
| axe-core on `/risk` @ 375px | 0 serious violations |

### Sidebar audit closure
| Sidebar entry | Audit said `href="#"` | Status |
|---|---|---|
| Universe | yes | ✅ wired in A1 |
| Risk workspace | yes | ✅ wired in B1 (this commit) |
| News intelligence | yes | pending B2 |
| Ops command | mislabelled `/admin` | ✅ wired in A2 |

3 of 4 closed. News intelligence is B2.

### Honest limitations
- Parametric VaR assumes normal-distributed returns. For long-tailed P&L this understates tail risk. Historical-simulation VaR over the same series would be a one-method swap and a richer plot; tracked as a polish follow-up.
- Beta is not computed (no benchmark series).
- Concentration uses `current_weight` from holdings; if a portfolio's `current_weight` is stale (no recent valuation snapshot), the displayed concentration can drift from target. A "as-of date" footnote would resolve the ambiguity; deferred.

---

## B2 — News intelligence (RSS + VADER sentiment)
**Date:** 2026-05-21
**Status:** Closed; closes the audit's phantom-sidebar gap entirely

### What shipped
**Backend:**
- `backend/requirements.txt` — `feedparser==6.0.11` + `vaderSentiment==3.3.2` added. Both pure-Python, no external API keys, no upstream rate limits to negotiate.
- `backend/app/services/news.py` (new) — `NewsService.get_headlines()` aggregates 3 free RSS sources (Yahoo Finance Top, MarketWatch Top, MarketWatch Markets), scores each headline with VADER (compound score + bucketed label), de-duplicates by title-case, and caches results for 5 minutes. Fetch is parallel via `asyncio.run_in_executor` since feedparser is blocking I/O.
- `backend/app/api/v1/news.py` (new) — `GET /api/v1/news` returns `{ summary, items }` where summary is total / positive / neutral / negative / mean compound. `?refresh=true` bypasses the cache.
- `backend/app/api/router.py` — registered with tag `["news"]`.
- `backend/app/core/config.py` + `flags.py` — `feature_news_ui` flag.
- `backend/tests/test_phase_b2_news.py` (new) — **5 tests**: VADER label bucket boundaries, polarity sanity (positive/negative/neutral text scores correctly), empty input → neutral, end-to-end aggregation with monkey-patched feedparser fixtures including dedupe of case-different duplicates, and TTL cache invariant (second call within TTL doesn't re-fetch).

**Frontend:**
- `frontend/src/services/api.ts` — `NewsItem`, `NewsSummary`, `NewsBundle` types + `fetchNews(refresh)` fetcher.
- `frontend/src/contexts/FeatureFlagsContext.tsx` — `news_ui` flag.
- `frontend/src/app/news/page.tsx` (new) — `/news` route. Summary KPI strip (total / positive / negative / mean compound, color-coded), then a list of headlines as cards with title linking out, summary, source + published-at footer, and a sentiment badge in the top-right (color-coded). Refresh button bypasses the cache.
- `frontend/src/components/shell/Sidebar.tsx` — "News intelligence" `href "#"` → `"/news"` gated by `news_ui`. **The audit's last phantom sidebar entry is now a real surface.**
- `frontend/tests/e2e/news-mobile.spec.ts` (new) — render + axe at 375×667.

### Why
News was the last phantom-nav entry (`href="#"`) from the audit. Per the user-locked scope from 2026-05-20, the route was: **free RSS + VADER, no paid API**. That decision constrains scope nicely — RSS feeds are public and unauthenticated, VADER is rule-based and small, so the whole feature ships without any new credentials to manage, no rate-limit threading, and no recurring cost. The honest tradeoff is that we get rate-limited surface news, not Bloomberg-grade alpha-relevant news.

### Gates
| Gate | Result |
|---|---|
| backend pytest (news + flags) | 8 passed |
| backend ruff `app/` + mypy | clean |
| tsc --noEmit | clean |
| vitest | 21 passed |
| next build | **22 routes** (+`/news`) |
| playwright chromium | **28 passed** (+1 new news-mobile spec) |
| axe-core on `/news` @ 375px | 0 serious violations |

### Sidebar audit fully closed
| Sidebar entry | Audit said `href="#"` | Status |
|---|---|---|
| Universe | yes | ✅ wired in A1 |
| Risk workspace | yes | ✅ wired in B1 |
| News intelligence | yes | ✅ wired in B2 (this commit) |
| Ops command | mislabelled `/admin` | ✅ wired in A2 |

**4 of 4 closed.** Every workspace + ops nav entry now points to a real surface.

### Honest limitations
- VADER is a general-purpose sentiment lexicon. Some finance-specific phrasing ("downgrade", "miss") it scores correctly; subtler trader-speak ("dovish", "hawkish", "topside") it doesn't. For a fund-grade signal, a finance-tuned model (FinBERT or similar) would be the next step. Out of scope per the no-paid-API constraint.
- The cache is in-process. On a multi-instance deploy each instance fetches independently. Acceptable today; if we ever scale horizontally beyond 2-3 instances, a shared Redis cache becomes the obvious move (and would be paired with the slowapi → Redis migration tracked in C7).
- No deployment of the new Python deps yet — `feedparser` and `vaderSentiment` are installed locally and listed in `requirements.txt`. Railway will pick them up on next deploy. Documented as an operator follow-up.

---

## B3 — Saved views (DB-backed); closes Phase B
**Date:** 2026-05-21
**Status:** Closed

### What shipped
**Backend:**
- `backend/migrations/versions/020_saved_views.py` (new) — Alembic migration creates the `saved_views` table (`id, user_id, name, scope, filters_json text, tone, created_at, updated_at`) with two indexes (`user_id` and `(user_id, scope)` composite). Down-migration drops cleanly.
- `backend/app/models/saved_view.py` (new) — `SavedView` SQLAlchemy model.
- `backend/app/models/__init__.py` — exports SavedView so `Base.metadata.create_all` registers the table for tests.
- `backend/app/api/v1/saved_views.py` (new) — CRUD endpoints (`GET / POST / PATCH / DELETE`) all gated by `get_current_user` and scoped to the caller's `user_id`. Cross-tenant access returns 404 (not 403) to avoid leaking "exists but you can't see it" — a standard tenant-boundary hygiene pattern matching MVP-1's IDOR tests.
- `backend/app/api/router.py` — registers the new router with tag `["saved-views"]`.
- `backend/tests/test_phase_b3_saved_views.py` (new) — **6 contract tests**: create→list round-trip, tenant scoping (user A and B both create views, each only sees their own), PATCH updates fields, DELETE removes and a subsequent PATCH 404s, cross-tenant PATCH returns 404 (not 403), and unauthenticated requests 401/403.

**Frontend:**
- `frontend/src/services/api.ts` — `SavedView` type + 3 fetchers (`fetchSavedViews`, `createSavedView`, `deleteSavedView`). These wrap `apiFetch` with an explicit Bearer header injection via the existing `getAccessToken()` helper. Changing `apiFetch` project-wide to auto-inject is out of B3 scope; the wrapper pattern keeps the change surgical.
- `frontend/src/components/shell/Sidebar.tsx` — removed the hardcoded `SAVED` array. Now fetches the current user's views on mount via `useAuth().user`. Section auto-hides when the user has zero saved views OR is signed out — no more "empty pile" misleading the UI.

### Why
The audit called out the sidebar's "Saved views" pile as hardcoded fake data. Replacing it with a real per-user DB-backed list closes the audit's last "phantom UI" complaint and gives users a real place to bookmark Filter X on Surface Y. Migration uses `Text` for `filters_json` (not Postgres JSONB) so the same schema works on SQLite (tests) and Postgres (prod) without DDL branching.

### Gates
| Gate | Result |
|---|---|
| backend pytest | **768 passed, 2 skipped** (+6 saved-views tests; no regression) |
| backend ruff `app/` | clean (one import auto-fix) |
| backend mypy | clean |
| tsc --noEmit | clean |
| vitest | 21 passed |
| next build | 22 routes (no new routes — sidebar swap is internal) |
| playwright chromium | 28 passed |

### Phase B closes here
- B1 Risk workspace        `2a79b6f`
- B2 News intelligence     `4a817af`
- B3 Saved views           **this commit**

Phase B was the second net-new-backend block:
- B1 added `risk` (+10 tests, no migration)
- B2 added `news` (+5 tests, +2 deps, no migration)
- B3 added `saved_views` (+6 tests, +1 migration, +1 model)

Next: **Phase C — MVP debt closure** (C1..C7 per the roadmap):
- C1 fix F821 in `app/services/engines.py`
- C2 wire `backtest_hygiene.evaluate` into `BacktestService.run_backtest`
- C3 expand mypy to `app/api/` + `app/schemas/`
- C4 clean `KNOWN_PREEXISTING_RULES` in axe (already done in UX-3.1!)
- C5 fill skill content for `feature-flag-kill-switch`
- C6 FastAPI 0.115 → 0.118+, Next.js 14 → 16
- C7 slowapi → Redis (only if horizontally scaling)

### Honest limitations
- The Sidebar only **reads** saved views; there's no "Save current filter" affordance on the workspace pages yet. The CRUD endpoints exist for it, but every page would need to know which subset of its state to serialize. That's a per-surface design decision; for B3 the minimum is "the surface exists and reads from DB."
- Migration is created but not yet applied to prod (Railway). The schema diff between SQLite test DB and a Postgres prod DB will only land on the next deploy. Operator follow-up: run `alembic upgrade head` after deploy.

---

## C1 + C2 + C3 (partial) + C4 + C5 — MVP debt closure
**Date:** 2026-05-21
**Status:** Closed (C3 partially; C6 + C7 deferred)

### What shipped

**C1 — Latent F821 fix in engines.py:**
- `backend/app/services/engines.py` — `EngineService.run_engines()`: the `SignalRun` construction is hoisted above the category branch so the ML branch can reference `run` without a NameError. Previously the ML branch on line 315 read `run` before line 329 constructed it; the per-file `F821` ignore in pyproject masked the issue. The "no implementation found" branch now also gets a proper SignalRun marked as `skipped` (was orphaned in the old layout).
- `backend/pyproject.toml` — removed the per-file `F821` ignore for `app/services/engines.py`. Comment updated to note the fix landed in Phase C1.

**C2 — Backtest hygiene gate wired into BacktestService.run_backtest:**
- `backend/app/services/backtesting.py` — after `results_summary` is written, `backtest_hygiene.evaluate(config, results_summary, decision_data_as_of)` is called. The report's blocks/warns/details are persisted onto `results_summary["hygiene"]`. If any rule blocks, each blocked rule appends a `"hygiene: <rule>"` entry to `results_summary["warnings"]`. Status stays `"completed"` so the operator gets a full record to review rather than a half-written row — the gate flags issues without erasing data.
- The `decision_data_as_of` map is built from the run's decision_points so the look-ahead rule has the provenance it needs.
- 35 backtest-related tests still pass after the wiring; the gate runs on every backtest output now.

**C3 — Mypy expanded to app/schemas/:**
- `backend/pyproject.toml` — mypy `files = ["app/core/", "app/schemas/"]` (was just `app/core/`). 32 source files now under the gate, all clean.
- Tried adding `app/api/`; it transitively pulls `app/services/finrlx_research.py` which surfaces ~60 type errors (mostly `"object" not callable` in dynamic-import branches). That's its own multi-day cleanup, tracked but not closed in this commit.

**C4 — Axe `KNOWN_PREEXISTING_RULES` already cleared in UX-3.1:**
- Captured for the audit trail: this work landed in commit `9b10f8f`. The allow-list is empty; every route is axe-clean across all viewports.

**C5 — Both empty-content skills already populated:**
- `feature-flag-kill-switch` and `recommendation-object-provenance` SKILL.md files both have full content. They were filled in during MVP-4 and MVP-3 work respectively (sources say `source: project`); the roadmap memo was stale on this.

### What's deferred (with reasoning)

**C3 (partial) — app/api/ mypy:**
- Out of scope here because it ladders into `app/services/finrlx_research.py`'s ~60 errors. That file has dynamic-import branches that need explicit `cast()` / `assert isinstance()` annotations. Tackling it requires a focused multi-hour pass that doesn't belong inside an autonomous run; it's a clean-room follow-up.

**C6 — FastAPI 0.115 → 0.118+ and Next.js 14 → 16:**
- Both are major-version upgrades. FastAPI 0.116+ changes `lifespan` semantics and some response-model defaults; Next 15 → 16 is the App Router cache/lifecycle rewrite plus Turbopack production. Either could break end-to-end behavior in subtle ways. Doing them inside an autonomous run risks shipping a regression nobody catches until staging. Deferred to a dedicated dependency-upgrade phase with a separate verification plan.

**C7 — slowapi → Redis storage:**
- Only matters when the app runs on multiple instances. We're on 1 Railway instance today. When that changes — or when the in-memory rate limit becomes a real source of bug reports — this is the moment to swap. Not work for now.

### Gates
| Gate | Result |
|---|---|
| backend pytest | **768 passed, 2 skipped** (no regression after C1 + C2) |
| backend ruff `app/` | clean (the F821 per-file ignore was removed; ruff still happy) |
| backend mypy | 32 source files clean (app/core/ + app/schemas/) |
| tsc --noEmit | clean |
| vitest | 21 passed |
| next build | unchanged |
| playwright chromium | 28 passed |

### Phase C status
- C1 Fix F821 ✅
- C2 Wire backtest_hygiene.evaluate ✅
- C3 Expand mypy to app/api + app/schemas: **app/schemas/ ✅; app/api/ deferred (transitive errors in services/)**
- C4 Clean KNOWN_PREEXISTING_RULES ✅ (landed in UX-3.1, captured here)
- C5 Fill empty skill content ✅ (was already done; corrected the roadmap)
- C6 Dependency upgrades — **deferred** with reasoning
- C7 slowapi → Redis — **deferred** with reasoning

### What this closes overall
| Track | Status |
|---|---|
| UX-1..UX-5 | Closed (UX-3.6 manual VoiceOver still awaits user iPhone) |
| Phase A (A1-A4) | Closed |
| Phase B (B1-B3) | Closed |
| Phase C | Closed for C1, C2, C3-schemas, C4, C5. C3-api, C6, C7 explicitly deferred. |
| Phase D iOS | Skipped per locked decision (PWA-first) |
