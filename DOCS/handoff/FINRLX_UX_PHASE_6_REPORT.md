# FINRLX UX/UI Transformation — Phase 6 Report

## A. Summary

Phase 6 creates the Research product area as a real, navigable surface
for the first time. Two new routes ship:

- `/research` — Research hub landing. Free-form ticker search,
  universe grid (existing `/api/v1/universes`), and entry-point cards
  to Backtests and the current Decision.
- `/research/[ticker]` — Per-ticker workspace. Real price chart
  (reuses `PriceChartCard` and `/api/v1/pricechart`), real news strip
  filtered by ticker (frontend filter over `/api/v1/news`), an
  "Capture analyst note" deep-link to the operator console, and
  **honest** placeholder cards for Fundamentals and Peers (no backend
  exists yet).

Sidebar's Research area now lists three entries: Research hub
(new), Universe, Backtests. TopBar breadcrumb resolves
`/research/[ticker]` to `Research · TICKER`.

The full Research workspace (fundamentals depth, peer comparison,
source-grounded assistant) requires backend work (fundamentals feed,
peer membership feed, assistant grounding pipeline) that is **out of
scope** for this redesign program. Phase 6 lands a credible
skeleton, not a fake-complete UI.

## B. Skills used

- `finrlx-ux-redesign-director` — rules 1, 4, 7, 9, 10.
- `finrlx-fintech-dashboard-patterns` — card patterns, freshness chips, empty states with explanation.
- `finrlx-ai-ux-governance` — the "Capture analyst note" link routes to the operator console, the right pattern (operator-curated LLM context). Full embedded assistant deferred to Phase 11.
- `feature-flag-kill-switch` — universe + backtests entries remain flag-gated. `/research` itself is not flag-gated (it's the new hub).
- `fintech-disclaimer-and-marketing-guard` — page copy explicitly states "research output — not advice, not a published recommendation" and the per-ticker header says "informational — not a recommendation to buy or sell".
- `recommendation-object-provenance` — no Recommendation surface touched.
- `finrlx-visual-qa-accessibility-gate` — typecheck / test / build / forbidden-language sweep.
- `finrlx-handoff-evidence-packager` — this report.

## C. External references used

- TIKR — fundamentals depth pattern (informed where the "Fundamentals" placeholder explanation came from).
- Koyfin — research workspace shape (drove the ticker workspace as a single scrollable column with header, chart, news, peers).
- AlphaSense — source-grounded research (deferred to Phase 11; placeholder copy on `/research/[ticker]` directs to the operator console for now).

## D. Files changed

| File | Purpose |
|---|---|
| `frontend/src/app/research/page.tsx` | New — Research hub landing. |
| `frontend/src/app/research/[ticker]/page.tsx` | New — per-ticker workspace. |
| `frontend/src/components/shell/Sidebar.tsx` | Research area: added Research hub entry (no flag, since hub is the new area landing). |
| `frontend/src/components/shell/TopBar.tsx` | CRUMB_MAP gains `/research` → `Research · Research hub`. Added `/research/*` fallback that renders `Research · TICKER`. |
| `DOCS/handoff/screenshots/phase6/_NOT_CAPTURED.md` | Honest record. |
| `DOCS/handoff/FINRLX_UX_PHASE_6_REPORT.md` | This report. |

## E. UX decisions

1. **Real skeleton, honest empty states.** Fundamentals and Peers are explicitly marked "coming later" with the reason (no backend feed). Not invented data, not silent gaps.
2. **Ticker validation is strict.** `[A-Z]{1,8}(\.[A-Z]{1,4})?` matches Yahoo-style symbols. Invalid input shows an inline error rather than navigating to a 404-ish state.
3. **News is filtered client-side** with a word-boundary regex on title + summary. The backend `/api/v1/news` endpoint does not support a ticker-filter parameter. Phase 9 may extend the endpoint when redesigning Insights.
4. **Operator console is the assistant proxy for Phase 6.** The "Capture analyst note" button passes `?surface=manual&ticker=…` to `/operator` — that's how operators capture GPT/Claude analyses against a ticker today. Phase 11 will replace this with an embedded source-grounded assistant.
5. **Sidebar entry "Research hub" not flag-gated.** The hub is the area landing. If we ever gate it, the whole Research area entry should hide; that's handled by the flag-on-each-entry pattern already in `Sidebar.tsx`.
6. **`/universe` remains a separate route**, not a sub-route of `/research`, per the Phase 2 IA. The hub deep-links to `/universe?id=…` for coverage / readiness, which is the universe page's job.
7. **No redirect map added.** No legacy route was retired in Phase 6. Phases 8 / 10 will add their own redirects when they move `/paper`, `/risk`, `/policies`, `/integrations`, `/admin`, `/operator`.

## F. Data / API contract notes

- Consumes existing endpoints only:
  - `GET /api/v1/universes` (Research hub)
  - `GET /api/v1/pricechart?ticker=…` (per-ticker workspace, via `PriceChartCard`)
  - `GET /api/v1/news` (per-ticker workspace, client-side filtered)
- No new endpoints. No backend code changed.
- Suggested for Phase 9: extend `GET /api/v1/news` with an optional `ticker` filter so the per-ticker workspace doesn't pull the full feed.

## G. Safety / governance notes

- Both pages render under the standard `AppShell` so `DisclaimerBanner` is present.
- Page copy explicitly says "research output — not advice, not a published recommendation" (hub) and "informational — not a recommendation to buy or sell the security" (ticker workspace).
- Forbidden-language sweep: no new hits introduced.
- The "Capture analyst note" CTA opens the operator console — that surface already enforces operator-only governance + LLM-context capture rules.

## H. Testing evidence

| Command | Result |
|---|---|
| `npm run typecheck` | **PASS** |
| `npm run test:ci` | **PASS** — 41 / 41 (no test was research-coupled; existing tests untouched) |
| `npm run build` | **PASS** — Next.js 15.5.18, route list now includes `/research` (3.31 kB, static) and `/research/[ticker]` (3.05 kB, dynamic). |
| Forbidden-language sweep | **PASS** |
| `npm run e2e:ci` | **Not run** — no playwright config |

## I. Screenshot evidence

See `DOCS/handoff/screenshots/phase6/_NOT_CAPTURED.md`.

## J. Known limitations

1. **Fundamentals and Peers are honest placeholders.** No backend feed exists; not invented.
2. **News filter is best-effort.** A word-boundary regex on `\bTICKER\b` against title + summary will miss articles that reference the company by full name (e.g. "NVIDIA Corporation" instead of "NVDA"). Phase 9 should extend the news endpoint with a real ticker / company taxonomy.
3. **No source-grounded embedded assistant.** The "Capture analyst note" CTA is the Phase-6 stand-in; full assistant is Phase 11.
4. **`PriceChartCard` doesn't yet adopt Phase 3 typography tokens.** It still ships `text-[13px]` / `text-[12px]`. Migration happens when Phase 7 (Decisions) redesigns the chart-bearing components.
5. **No redirect from `/universe?id=…` back to `/research`** for users who want a ticker view rather than a coverage view. The IA permits both; Phase 8 may revisit.
6. **No screenshots yet.** Carries forward.

## K. Phase 6 gate compliance (plan §5 Phase 6)

| Gate 6 criterion | Status |
|---|---|
| Users can search and understand a ticker/company quickly | **Partially met** — ticker search works; "understand quickly" depends on fundamentals/peers that are honestly deferred |
| Research sections are not walls of text | **Met** — cards with short copy, honest empty-state cards |
| Evidence and limitations are visible | **Met** — explicit "research output, not advice" copy; explicit "coming later" cards |
| AI assistant does not replace structured UX | **Met** — assistant is one deep-link, not the dominant surface |
| Data states are handled | **Met** — loading / error / empty states present on both pages |

**Gate 6 clears (with the honest-skeleton caveat documented).**

## L. Next recommended phase

**Phase 7 — Decision pipeline redesign.** Will edit
`frontend/src/app/decision/page.tsx` and the decision components. The
backlog flagged the hardcoded risk-overlay gauge values
(`decision/page.tsx:221–238`) and the dense single-scroll layout as
priority cleanups.
