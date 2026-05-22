# FINRLX UX/UI Transformation — Phase 2 Navigation Spec

> Required by `DOCS/FINRLX_UX_UI_TRANSFORMATION_MASTER_PLAN.md` §5 Phase 2.
> This file specifies the shape of navigation, breadcrumbs, the command
> palette, and the mobile drawer that Phase 4 will implement. **No code
> ships in Phase 2.**

## 1. Sidebar (desktop ≥ 768 px)

### Structure

```
┌─────────────────────────┐
│ FINRLX             v0.3 │ ← brand row (44 px)
├─────────────────────────┤
│ 🏠 Home                 │
│ 🔬 Research             │
│ 🎯 Decisions       (3)  │  ← badge from /overview workspace count
│ 💼 Portfolio & Risk     │
│ 📰 Insights        (8)  │  ← badge from /insights unread count
│ ⚙️  Ops & Governance     │
├─────────────────────────┤
│ ⚡ Settings              │  ← lower-priority anchor
├─────────────────────────┤
│ Saved views             │  ← only if signed-in & user has views
│  • Conservative Q3      │
│  • Tech megacaps        │
├─────────────────────────┤
│ v0.3.0                  │  ← version footer
└─────────────────────────┘
```

### Behavior

- Default width: 208 px (`w-52`). Collapsed width: 56 px (`w-14`).
- Collapse toggle in `TopBar`. State persists in `localStorage`.
- Active state: matches the area, not the exact path. `/decision/abc` lights up "Decisions".
- `aria-current="page"` on the active entry.
- Counts come from existing `fetchWorkspaceCounts` (extended in Phase 4 to cover Insights and Portfolio & Risk).
- Gated entries hide while flags load (`feature-flag-kill-switch`).
- Keyboard: `Tab` cycles through entries; `Enter` activates.

### Removed from sidebar (vs current state)

The following current sidebar entries leave the sidebar — they live in-page or under their area's sub-nav:

- Engine comparison → Decisions sub-tab.
- Replay & forensics → Decisions sub-tab.
- Backtests → Research sub-tab.
- Universe → Research sub-tab.
- Policies → Ops sub-tab.
- Integrations → Ops sub-tab.
- Research lab → Ops sub-tab (`/ops/lab`).
- Send feedback → Settings sub-tab (or kept at root for beta).
- My profile → Settings sub-tab.

Result: sidebar shrinks from 16 entries to 7 + saved views.

## 2. TopBar

```
┌───────────────────────────────────────────────────────────────────────────┐
│ [≡] FINRLX  Decisions · NVDA · Compare      [ ⌘K Search ]  [Aa] [☾] [?] ▢ │
└───────────────────────────────────────────────────────────────────────────┘
```

### Slots

- **Brand** — FINRLX logo + name. Brand color square.
- **Breadcrumb** — `Area · Sub-area · Current`. Max three crumbs.
- **Scope chips** (desktop ≥ `lg`) — Regime · Horizon · Universe. Already present today, keep.
- **Command palette trigger** — visible chip with `⌘K` shortcut.
- **Density cycle** (`Aa` button).
- **Theme toggle** (sun / moon).
- **Help center shortcut** (`?`).
- **Notifications** (bell with breach dot).
- **Context pane toggle** (right rail).
- **User menu** (avatar + dropdown).

### Mobile (< 768 px)

- Brand + nav toggle + breadcrumb (truncated to one segment).
- Right side: theme + user menu only. Density / help / notifications / context-pane / palette move into the user menu or the mobile drawer.
- Command palette opens via long-press on the nav toggle, or via the user menu.

## 3. Mobile drawer

- Slides in from the left when the user taps the nav toggle.
- Width: 256 px (`w-64`).
- Same seven entries as the desktop sidebar, full-width labels.
- Saved views section visible if the user has any.
- Tap-outside or tap-on-link closes the drawer.
- Backdrop: `bg-ink/40 backdrop-blur-sm`.
- No icon-only mode on mobile.

## 4. Command palette (⌘K, Ctrl+K)

### Behaviour

- Opens a modal centered on the viewport.
- Renders a search field, a category strip, and a results list.
- Closes on `Esc`.
- Restores focus to the trigger on close.

### Categories (in order)

1. **Routes** — the seven product areas + sub-routes the user has access to.
2. **Tickers** — last-search history first; then live search via `/research?q=…`.
3. **Recommendations** — recent recommendations by id / status; opens `/decision/[id]`.
4. **Operator analyses** — recent `OperatorAnalysis` rows; opens `/ops/operator?id=…`.
5. **Help** — full-text search over `frontend/help/**/*.mdx` content.

### Visual contract

- Top input: 16 px font (mobile-safe), `Search FINRLX…` placeholder.
- Result row: 14 px label, 12.5 px secondary, 11 px category chip on the right.
- Selection state: `bg-primary-soft text-primary-soft-ink`.
- Keyboard: arrow keys move; `Enter` selects; `Tab` swaps category.
- Empty: "Type to search. Try a ticker symbol, a route, or a recommendation id."

### Phase 4 implementation cue

A `CommandPalette` already exists in `frontend/src/app/admin/_components/CommandPalette.tsx`. Phase 4 should evaluate whether to lift that component to `frontend/src/components/shell/CommandPalette.tsx` and extend it, or build a fresh one. Either is fine; do not ship two.

## 5. Breadcrumbs

- Render in TopBar between the nav toggle and the spacer.
- Three slots max: `Area · Sub-area · Current`.
- Each crumb is a link to that level.
- Truncate middle crumb with `…` if the total exceeds the TopBar slot width.
- Hide entirely on mobile (< 768 px) — the user menu drops a "where am I" hint instead.

## 6. Sub-navigation per area

| Area | Sub-nav style | Items |
|---|---|---|
| Home | none | — |
| Research | in-page tabs above the workspace | Overview · Fundamentals · Technicals · News · Peers · Assistant · Universe · Backtests |
| Decisions | in-page tabs | Current · Evidence · Compare · Replay · History |
| Portfolio & Risk | in-page tabs | Paper · Risk · Scenario · Exposure |
| Insights | filter chips (not tabs) | Watchlist · Portfolio · Decision-impacting · Risk · Macro |
| Ops & Governance | in-page tabs | Health · Queue · Policies · Integrations · Lab · Operator · Audit |
| Settings | left sub-nav | Profile · Help · Account · Beta feedback |

## 7. Accessibility contract

- `<nav aria-label="Primary">` wraps the sidebar.
- `<nav aria-label="Breadcrumb">` wraps the TopBar breadcrumb.
- `<nav aria-label="Sub-navigation">` wraps each area's in-page tab bar.
- Skip-to-content link (already present at `AppShell.tsx:58–63`) stays.
- Focus ring visible on every nav entry.
- All touch targets ≥ 44 px on mobile.
- No keyboard trap on the mobile drawer or the command palette.
- Live region on the area badge counts (`role="status"`).

## 8. Implementation cues for Phase 4

These are not Phase 2 work — they are notes for Phase 4 so the spec is unambiguous.

- The two arrays `WORKSPACES` and `OPS` in `frontend/src/components/shell/Sidebar.tsx` collapse into one `AREAS` array of 7 entries.
- `Sidebar.tsx` no longer needs feature-flag rows for individual sub-routes; that logic moves into each area's sub-nav component.
- `TopBar.tsx` adds a breadcrumb slot and a real command-palette trigger (currently it is a placeholder).
- `next.config.js` (or `next.config.mjs`) grows a `redirects()` block covering every row in `FINRLX_UX_PHASE_2_ROUTE_MIGRATION_MAP.csv`.
- A new `app/research/` directory is created in Phase 6; in Phase 4, only the route stub + sub-nav lives.
- The existing admin command palette is the seed for the global one; lifting it is preferred over re-writing.

## 9. Gate 2 (navigation) — summary

This spec answers every Gate 2 navigation question:

- Mobile navigation defined: §3.
- Command palette behaviour defined: §4.
- Breadcrumbs defined: §5.
- Sub-nav per area defined: §6.
- Accessibility contract defined: §7.

Phase 4 implements the spec. Phase 4's gate is implementation correctness against this document.
