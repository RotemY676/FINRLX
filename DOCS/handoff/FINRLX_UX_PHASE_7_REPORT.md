# FINRLX UX/UI Transformation — Phase 7 Report

## A. Summary

Phase 7 is a truth-and-trim pass on `/decision`. Two long-standing
issues from the Phase 0 redline backlog get fixed:

1. **D-3 — Hardcoded risk-gauge mock removed.** Previous code rendered
   five fake gauge rows (Portfolio weight 42/60, Sector concentration
   81/75, etc.) alongside the real `stages.risk_overlay.rationale` and
   `adjustments`. The mock has been replaced with the **real**
   `portfolio_risk_score` plus the real `constraints_applied` chip
   list. No invented numbers.
2. **D-4 — Dead secondary actions trimmed.** Bookmark, Share, and More
   buttons had no `onClick`. They're removed. Compare and Replay had
   no handlers either, but the routes (`/comparison`, `/replay`) exist
   — they're converted to real `<a>` links instead of dead buttons.

Phase 7 also migrates the Decision page section headers to the Phase 3
named typography tokens (`text-section-title`, `text-card-title`,
`text-caption`).

The bigger Phase 7 ambitions from the plan — id-based deep linking via
`/decision/[id]`, splitting the long scroll into a hero + ContextPane,
historical recommendation list — are **deferred** because they need
backend changes (a `GET /api/v1/recommendations/{id}` endpoint exists
in the route registry but is wired only for the current rec via
`fetchCurrentRecommendation`; a list endpoint also exists but isn't
yet typed on the frontend). Phase 7 here ships truthful cleanups, not
a redesign.

## B. Skills used

- `recommendation-object-provenance` — the iron rule: every Recommendation render must be tamper-evident and source-grounded. Hardcoded mock values violated this; they're gone now.
- `fintech-disclaimer-and-marketing-guard` — verified the page still ships only safe CTA copy ("Save as current thesis", "Promote to paper", "Defer decision"). No execution language.
- `finrlx-ux-redesign-director` — rules 4 (readable density), 7 (no execution language), 10 (evidence not optional).
- `finrlx-fintech-dashboard-patterns` — risk score becomes a single named number; `constraints_applied` are semantic chips, not invented gauges.
- `feature-flag-kill-switch` — `/decision` isn't flag-gated. Untouched.
- `replay-determinism-harness` — no replay surface changed.
- `finrlx-visual-qa-accessibility-gate` — typecheck / test / build / forbidden-language sweep.
- `finrlx-handoff-evidence-packager` — this report.

## C. External references used

None new. Phase 0 §1.10 (NN/g dashboards, single-number "Smart Score" anti-pattern) reinforced the decision to surface `portfolio_risk_score` as one number and let the `constraints_applied` chips carry the detail.

## D. Files changed

| File | Purpose |
|---|---|
| `frontend/src/app/decision/page.tsx` | Removed hardcoded risk gauge array (was lines 221–226). Replaced with backend-fed `portfolio_risk_score` + `constraints_applied` chips. Removed Bookmark / Share / More dead buttons. Converted Compare / Replay buttons to `<a href>` links. Migrated three section headings to Phase 3 typography tokens. |
| `DOCS/handoff/FINRLX_UX_PHASE_7_REPORT.md` | This report. |

No screenshot directory created for Phase 7; the visible delta is
removal of mock data + a typography bump — captured at Phase 12 with
the rest.

## E. UX decisions

1. **Show the truth, even when the truth is "no data".** If `portfolio_risk_score`, `constraints_applied`, and `adjustments` are all empty, the page now says "Risk overlay ran but reported no constraints, score, or adjustments for this recommendation" instead of inventing gauge values to fill the panel.
2. **Compare / Replay become anchor links.** They already navigated visually like buttons but had no handlers. Anchors with `href` are the correct semantic and a11y choice; the previous `<button>` with no `onClick` was an a11y violation (button announces but does nothing).
3. **Bookmark / Share / More disappear entirely.** Per the playbook anti-patterns list: "phantom affordances" are forbidden. If a feature isn't built, don't ship a button for it.
4. **Did not add `/decision/[id]`.** The backend has the data (`fetchCurrentRecommendation` is one of several recommendation endpoints), but `RecommendationDetail` doesn't expose the same `data_as_of`, `disagreement`, etc. that the current view consumes. Phase 7 here keeps the scope honest — id deep linking is a follow-up phase, not this one.
5. **Did not split the page into hero + ContextPane.** The page is long, but splitting is a substantial restructure that risks breaking the operator's existing scan pattern. Deferred to a later UX phase when there's user testing data to justify the split.

## F. Data / API contract notes

- Reads `stages.risk_overlay.portfolio_risk_score` and `stages.risk_overlay.constraints_applied` — these were already in `RiskOverlayView` (see `frontend/src/services/api.ts:161–169`). No backend contract change.
- Page still renders correctly when these fields are `null` / empty.

## G. Safety / governance notes

- The recommendation hero, `ConfidenceBlock`, evidence narrative, disagreement, warnings, weights, positions, and metadata — all still source-grounded from the backend and unchanged.
- `DisclaimerBanner` still ships via `AppShell`.
- Forbidden-language sweep: no new hits.
- `recommendation-object-provenance` iron rule: every recommendation render is tamper-evident. Phase 7 removes the one place that wasn't (hardcoded gauges).

## H. Testing evidence

| Command | Result |
|---|---|
| `npm run typecheck` | **PASS** |
| `npm run test:ci` | **PASS** — 41 / 41 (no test was decision-gauge-coupled; the change is content removal not contract change) |
| `npm run build` | **PASS** — same route count as Phase 6 (78 routes total: 77 static + 1 dynamic) |
| Forbidden-language sweep | **PASS** — no new hits |
| `npm run e2e:ci` | **Not run** — no playwright config |

## I. Screenshot evidence

Not captured. The visible delta on `/decision` is real (the entire risk-constraints panel changed shape), and Phase 12 will be the first phase where I invest meaningfully in a screenshot pipeline. Recording this honestly in the handoff so it does not get glossed over.

## J. Known limitations

1. **No `/decision/[id]`.** Deferred to a follow-up phase. Today the page is "the current recommendation" only.
2. **No long-scroll restructuring.** The hero + evidence + disagreement + warnings + chart + weights + positions + risk + scenario + pipeline + metadata stack is still tall. Phase 12 may revisit.
3. **No audit-trail drawer.** Plan §5 Phase 7 step 5 called for "audit trail drawer" — the existing `ContextPane` infrastructure could host one, but wiring it requires a backend audit endpoint per recommendation that the frontend doesn't yet consume. Deferred.
4. **Phase 7 does not implement a "gate checklist".** Plan §5 Phase 7 step 6 — the publication gates exist in backend `publication.py` but the frontend doesn't yet surface them per recommendation. Phase 10 (Ops & Governance redesign) will expose them in the ops surface.
5. **No screenshots captured.** Carries forward.

## K. Phase 7 gate compliance (plan §5 Phase 7)

| Gate 7 criterion | Status |
|---|---|
| Every recommendation state is visually distinct | **Met** — `StatusBadge` already renders distinct visual states. Unchanged. |
| Blocked states explain why | **Partially met** — `WarningsBlock` shows warnings; explicit "blocked" state is a backend concept not yet surfaced. Honest gap. |
| Provenance is visible | **Met** — `MetadataBlock`, `SourceBadge`, `data_as_of` in hero. Unchanged. |
| Risk overrides are not hidden | **Improved** — the per-position adjustments list is now under a clear "Per-position adjustments" heading instead of mixed with mock gauges. |
| Publication gates are readable | **Not met** — deferred to Phase 10. |
| No unsafe investment language | **Met** — forbidden-language sweep clean. |

**Gate 7 is partially met.** Three criteria fully pass, two are improvements, one is deferred. The mock-removal and dead-button-removal address two explicit Phase 0 backlog items (D-3, D-4). Honest improvement, not a full Phase 7 implementation.

## L. Next recommended phase

**Phase 8 — Portfolio & Risk redesign.** Will edit `/paper`, `/risk`, and may introduce the `/portfolio` tabbed landing per the Phase 2 IA. Focus on grouping the existing two surfaces, applying typography, and adding the redirects map (`/paper` → `/portfolio/paper`, `/risk` → `/portfolio/risk`).
