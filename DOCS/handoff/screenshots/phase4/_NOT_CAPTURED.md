# Phase 4 — Screenshots not captured

Phase 3 left an `_NOT_CAPTURED.md` marker because the production server
did not bind within the polling window. Phase 4's edits are visually
real (sidebar regrouping, breadcrumb redesign), but the screenshot
matrix was again not run in this session — the user explicitly asked
me to stop the monitor / background-server probe and continue.

Recorded honestly. Visual evidence for the seven-area sidebar and the
area-aware breadcrumb will be captured at the next opportunity (Phase
5 home-redesign visual gate is the natural place).

## What changed visually

- Sidebar: 16 entries reorganized into seven `<section role="group" aria-labelledby>` blocks under "Home / Research / Decisions / Portfolio & Risk / Insights / Ops & Governance / Settings".
- Sidebar: active entry now carries `aria-current="page"`.
- Sidebar: section headings use `text-meta` (12.5 px) instead of the previous 10 px ad-hoc size.
- Sidebar: badge text uses `text-meta` instead of 11 px ad-hoc.
- TopBar: single-string crumb replaced with a semantic `<nav aria-label="Breadcrumb"><ol>` showing `Area · Page` when applicable.

## Verification done in lieu of screenshots

- `npm run typecheck` — pass.
- `npm run test:ci` — 41 / 41 pass (no test was sidebar-coupled enough to break).
- `npm run build` — 76 / 76 static pages generated; same routes; bundle sizes within ±200 bytes of the Phase 3 baseline.
