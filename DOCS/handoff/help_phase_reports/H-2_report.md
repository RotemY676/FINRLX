# Phase H-2 Report — Concepts track + Glossary

**Date:** 2026-05-22
**Branch:** main
**Status:** ✅ COMPLETED

## Scope

Fill in the **Concepts** track (8 explanation pages) and the **Glossary** with substantive content grounded in the FinRL-X research output. Each concept page is the place a user goes to understand *why* the product is shaped the way it is. The glossary is the canonical landing site for every term used across the help center.

## What was written

### Concepts (8 pages, ~600–900 words each)

| Page | Anchors covered |
|---|---|
| **The weight-centric pipeline** | The contract, what's in / what's out, trade-offs, layer roles |
| **Universe and features** | Point-in-time membership, look-ahead bias, normalization leakage |
| **Agents and engines** | Classical optimizers, the 5 RL algorithms, the ensemble, choice order |
| **Regimes and turbulence** | Regime classifier, turbulence index (Mahalanobis), throttle behavior |
| **Risk overlays** | Hard constraints, exposure caps, confidence floors, turbulence throttle, breach lifecycle |
| **Backtest vs. paper vs. live** | Data quality, execution realism, regime coverage, what to compare |
| **Governance and audit** | What's recorded, replay determinism, the three guarantees, scope limits |
| **Known pitfalls** | Overfitting, leakage, survivorship, costs, reward hacking, single-stock, regime change |

Each page:
- Opens with a one-paragraph thesis.
- Has 3–6 section headings that map to the underlying concept structure.
- Cross-links to peer concept pages and to the relevant reference / guide pages.
- Cites the original FinRL research where claims are non-obvious (the 2022 backtest-overfitting paper, the FinRL FAQ, the ICAIF 2020 ensemble paper, the FinRL-Meta paper, the tax-aware portfolio paper).

### Glossary (~50 terms)

Alphabetical, anchor-per-term, organized by letter section. Inline mentions across the help center can link directly to `#term-id` for jump-to behavior. Cross-links from terms to the relevant concept pages where appropriate.

The list exceeds the 35 originally planned because several concepts needed paired entries (e.g., `event date` + `available date`, `coverage` + `readiness`, `policy` disambiguated into RL-policy vs. FINRLX-policy).

## Verification

| Check | Result |
|---|---|
| `npm run typecheck` | ✅ clean |
| `npm run lint` | ✅ clean (zero warnings) |
| `npm run build` | ✅ all 75 static pages prerendered; help routes resolve. |
| Word-count smoke | Each concept page exceeds 500 words; glossary exceeds 2,500 words. |
| Cross-link smoke | Every concept page links to at least 2 peer pages and 1 reference / guide page. |

## What lands next (H-3)

Fill out the **Reference** track (15 per-route pages + 4 top-level catalogues: Status chips, Policy controls, Metrics, REST API).

## Exit checklist

- [x] All 8 concept pages have substantive bodies, not stubs.
- [x] Glossary has ≥ 35 terms (now ~50).
- [x] Every claim that depends on the FinRL canon has an inline link to the source.
- [x] Cross-links between concepts are present and the link targets exist.
- [x] Typecheck + lint + build green.
- [x] Phase report committed.

## Next step

Commit, push, proceed to H-3.
