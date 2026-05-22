# Phase 6 — Screenshots not captured

Fourth phase. Dev-server screenshots have not been viable in this
Windows session and the user explicitly asked to stop monitor
experiments. Phase 6 visual deltas (a new `/research` landing and a
new `/research/[ticker]` workspace) will be captured at Phase 12 along
with the rest of the redesigned surfaces.

## Verification done in lieu of screenshots

- `npm run typecheck` — pass.
- `npm run test:ci` — 41 / 41 pass (no new tests added in Phase 6; existing tests unaffected).
- `npm run build` — pass. Static pages: 76 + 1 new static (`/research`) + 1 new dynamic (`/research/[ticker]`) = 77 static / 1 dynamic.
- Sidebar Research area now lists three entries: Research hub (new), Universe, Backtests.
- Breadcrumb resolves `/research/NVDA` → `Research · NVDA` via the TopBar `/research/*` fallback.
