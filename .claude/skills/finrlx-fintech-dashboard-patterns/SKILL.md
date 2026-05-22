---
name: finrlx-fintech-dashboard-patterns
description: Canonical patterns for FINRLX dashboards, cards, tables, badges, charts, and KPI strips. Activates on any change under frontend/src/components/home/**, frontend/src/components/recommendation/**, frontend/src/components/charts/**, frontend/src/components/ops/**, frontend/src/components/universe/**, or any new dashboard/table/chart anywhere in frontend/src/components/**. Enforces freshness, provenance, action relevance, density-aware tables, and semantic risk/status badges.
type: project
---

# FINRLX — Fintech Dashboard Patterns

## When to invoke

- Any new or modified component that renders metrics, KPIs, tables, charts, heatmaps, or status grids.
- Any page that composes those components into a workspace (home, research, decision, portfolio, risk, insights, ops).
- Any change to `frontend/src/components/feedback/**` (loading / empty / error / stale) since the data-state contract lives there.

## Required props on every data component

Every component that renders a remote number must accept (or otherwise expose) all of:

- `asOf` — ISO timestamp of the data point shown.
- `status` — one of `fresh | stale | unavailable | partial | shadow-only`.
- `source` — engine / dataset name (e.g. `selection_v2`, `Frankfurter-FX`, `RSS:Yahoo`).
- `unit` — `%`, `bps`, `USD`, `count`, `ratio`, or `unitless`.
- `delta` — optional signed change with the same unit.
- `freshnessLabel` — short string (≤ 14 chars) for chip display, e.g. `2m ago`, `stale`, `n/a`.

The existing `DataFreshnessBadge` (`frontend/src/components/home/DataFreshnessBadge.tsx`) is the canonical chip; reuse it.

## Required states on every data-heavy component

1. **Loading** — `Skeleton` (`frontend/src/components/feedback/Skeleton.tsx`) sized to the resting shape.
2. **Empty** — `PageEmpty` for full-page, inline empty card otherwise. Always tell the user what to do next.
3. **Error** — `PageError` for full-page, inline error pill otherwise. Show the message; do not swallow it.
4. **Stale** — caution-tinted chip; render the stale value next to it. Never hide stale data.
5. **Shadow-only** — explicit ribbon: "Research-only, not published". Owned by the `recommendation-object-provenance` skill.
6. **Partial** — when only some sources reported. Show count `N of M` and which are missing.

## Tables

- Default text size: 14 px. Header: 12.5 px medium. Numeric columns: tabular-nums.
- Density mode: respect `--dens-row` (`compact` 30 / `default` 36 / `comfortable` 42 px).
- Mobile (< 768 px): table becomes a stacked card list with the same row contract. Use `display: block` containers, not horizontal scroll, unless the table is explicitly desktop-only.
- Empty / error / stale states render inside the table area, not as page-level toasts.
- Every row that links to a deeper view must be keyboard-navigable.

## Charts

- Axes always labeled with unit and last point's `as_of`.
- Use the semantic palette (`pos` / `caution` / `breach` / `accent` / `accent-2`). Never raw HTML colors.
- `prefers-reduced-motion` removes line-draw animation.
- Tooltip shows: value, delta, unit, source, freshness — in that order.

## KPI strip

- 2 columns on mobile, 4 columns on tablet, up to 6 on desktop.
- Each tile: label (12.5 px caption) + value (20–24 px display) + sub-line (caption).
- Tiles never render a single number without a unit and a freshness chip.

## Badges (semantic)

| Token | Use |
|---|---|
| `pos` / `pos-soft` | "ok", "fresh", "promoted" |
| `caution` / `caution-soft` | "stale", "warning", "partial" |
| `breach` / `breach-soft` | "blocked", "error", "policy-violation" |
| `primary` / `primary-soft` | active, navigational, "current" |
| `accent` / `accent-2` | research-only, model-comparison, shadow |

Never invent a new color for a badge. If you need a new semantic, add it to `globals.css` and the table above in the same change.

## Anti-patterns

- KPI tiles with no unit.
- Tables that scroll horizontally on mobile without an explicit `data-density="dense"` opt-in.
- Charts whose tooltips show only the raw value.
- "Status" pills that use only color (must also carry a short word).
- Aggregated "score" tiles that hide their components.

## Reuse list — do not duplicate

| Pattern | Existing component |
|---|---|
| Freshness chip | `frontend/src/components/home/DataFreshnessBadge.tsx` |
| Confidence trio | `frontend/src/components/recommendation/ConfidenceBlock.tsx` |
| Recommendation card | `frontend/src/components/recommendation/RecommendationCard.tsx` |
| Weights table | `frontend/src/components/recommendation/WeightsTable.tsx` |
| Warnings | `frontend/src/components/recommendation/WarningsBlock.tsx` |
| Source provenance | `frontend/src/components/recommendation/SourceBadge.tsx` |
| Status pill | `frontend/src/components/recommendation/StatusBadge.tsx` |
| Skeleton | `frontend/src/components/feedback/Skeleton.tsx` |
| Empty state | `frontend/src/components/feedback/PageEmpty.tsx` |
| Error state | `frontend/src/components/feedback/PageError.tsx` |
| Loading state | `frontend/src/components/feedback/PageLoading.tsx` |
