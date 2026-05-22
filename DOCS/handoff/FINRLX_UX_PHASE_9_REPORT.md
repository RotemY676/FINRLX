# FINRLX UX/UI Transformation — Phase 9 Report

## A. Summary

Phase 9 lands a working sentiment filter on `/news` plus a typography
migration. The filter is frontend-only (the backend `/api/v1/news`
does not yet support a sentiment query parameter); honest empty
state when a filter removes all items. The "Insights" rename
(`/news` → `/insights`) and the decision-linking work (per-watchlist
filter, "why this matters" summaries) are **deferred** — both require
backend taxonomy changes outside this redesign program's scope.

## B. Skills used

- `finrlx-fintech-dashboard-patterns` — sentiment chips remain semantic, every item now carries source + freshness, the filter chips use semantic `aria-selected`.
- `finrlx-ux-redesign-director` — rules 1, 4.
- `fintech-disclaimer-and-marketing-guard` — no execution language; sentiment scoring is explicitly labelled "VADER (rule-based, no external API)".
- `vercel-web-design-guidelines-mirror` — `aria-selected` on the filter chips, `role="tablist"` on the strip, U+2212 minus sign in the compound range copy.
- `finrlx-visual-qa-accessibility-gate` — typecheck / test / build / forbidden-language sweep.
- `finrlx-handoff-evidence-packager` — this report.

## C. External references used

None new. Phase 0 §2.5 (Finviz alternative search frustration) and §2.6 (AI-generated UI consistency) informed the decision to keep the news page as a dense scannable list rather than redesigning into "feed cards" that mimic social media.

## D. Files changed

| File | Purpose |
|---|---|
| `frontend/src/app/news/page.tsx` | Added `SentimentFilter` state + filter chip strip (All / Positive / Neutral / Negative with counts). Empty state explains the filter behaviour. Typography migrated to Phase 3 named tokens. U+2212 minus sign in the compound range disclaimer. |
| `DOCS/handoff/FINRLX_UX_PHASE_9_REPORT.md` | This report. |

## E. UX decisions

1. **Frontend filter, honest about it.** The backend doesn't yet support sentiment filtering. Doing it client-side is correct for the current dataset size and explicitly labelled in the page's "why this matters" disclaimer at the bottom.
2. **Counts visible on every chip.** A chip without a count makes the filter feel like a guess. With counts, the user knows what they will see before they click.
3. **No "Insights" rename in Phase 9.** Renaming the route would break legacy bookmarks. The IA migration map (Phase 2) records the eventual `/news` → `/insights` 308 redirect; landing it requires a `next.config.js` redirects block, which lives with the broader Phase 10 redirect rollout.
4. **`role="tablist"` + `aria-selected` instead of `aria-pressed`.** The filter mutates the visible list — semantically tabs, not pressed buttons.
5. **U+2212 minus sign.** Three places: the chip strip's compound footer ("[−1, 1]", "≥ 0.05", "≤ −0.05"). ASCII hyphens read as dashes in numeric ranges; the Unicode minus sign is the correct typography per the Vercel mirror rule.

## F. Data / API contract notes

None changed. Suggested extension for a future phase: `GET /api/v1/news?sentiment=positive&ticker=…` so the filter can scale beyond the small in-memory dataset.

## G. Safety / governance notes

- Per-item link still opens `target="_blank" rel="noopener noreferrer"`.
- Sentiment value uses semantic tokens (`pos-soft` / `breach-soft` / `surface-3` for neutral).
- Forbidden-language sweep: no new hits. The VADER disclaimer at the bottom keeps "positive ≥ 0.05" but that's mathematical, not marketing.

## H. Testing evidence

| Command | Result |
|---|---|
| `npm run typecheck` | **PASS** |
| `npm run test:ci` | **PASS** — 41 / 41 |
| `npm run build` | **PASS** — 78 routes; one pre-existing lint warning fixed (`react/no-unescaped-entities` on the empty-state copy I authored, immediately corrected with `&ldquo;` `&rdquo;`) |
| Forbidden-language sweep | **PASS** |
| `npm run e2e:ci` | **Not run** — no playwright config |

## I. Screenshot evidence

Not captured. Phase 12 will collect the full matrix.

## J. Known limitations

1. **`/news` → `/insights` rename not landed.** Deferred until the `next.config.js` redirects block lands in Phase 10.
2. **No "why this matters" summary** per item. Adding it requires either an LLM grounding step or an operator-curated annotation layer. Out of scope.
3. **No watchlist / portfolio / decision filter.** Same reason as above — backend taxonomy.
4. **Frontend filter scales only to the news cache window** (5 min RSS cache, ~50–100 items typically). If the dataset grows, the filter needs backend support.

## K. Phase 9 gate compliance

| Gate 9 criterion | Status |
|---|---|
| Insights linked to decisions or research context | **Not met** — deferred (backend) |
| Generic noise is reduced | **Partially met** — sentiment filter lets users carve the feed |
| Users can filter and act | **Met** — frontend chip filter ships |
| AI summaries are source-grounded or labelled as summaries | **Met** — VADER attribution explicit in the footer |

**Gate 9 partially met. Decision-linking is the right work to do in a follow-up backend phase, not invented here.**

## L. Next recommended phase

**Phase 10 — Ops & Governance polish + redirects rollout.** Touches `/ops`, `/policies`, `/integrations`, and lands `next.config.js` with the redirects for `/comparison`, `/replay`, `/news` → `/insights`, `/paper`, `/risk`, `/policies`, `/integrations`, `/admin`, `/operator`, `/profile`. Each redirect points to the *current* canonical path (no new sub-routes invented) — the redirect rollout is purely about future-proofing legacy bookmarks against the broader IA migration.
