---
title: Manage your universe
summary: Add or remove assets, check coverage and readiness, and avoid silent biases.
diataxis: how-to
area: guides
updated: 2026-05-22
order: 8
---

Your universe is the list of tradable assets every engine sees. The [Universe page](/help/reference/pages/universe) is where you manage it.

## Add an asset

1. Open [Universe](/help/reference/pages/universe).
2. Select the universe you want to modify.
3. Click **Add asset** in the toolbar.
4. Type the ticker; the autocomplete suggests matches.
5. Pick the effective date — usually today.
6. Confirm.

The asset enters the universe in **Warming up** state. Once the lookback window has been populated (typically 3–6 months for daily strategies), it transitions to **Ready** and becomes eligible for engine output. Until then it is *visible* in the universe but *excluded* from recommendations.

## Remove an asset

1. From the universe detail panel, click the row for the asset to remove.
2. Click **Remove** in the row's action menu.
3. Pick the effective date.
4. Confirm.

A removed asset stays in the membership history so past recommendations remain replayable. Future recommendations exclude it.

## Read coverage and readiness

- **Coverage** answers "do we have data?" A green chip means the feature pipeline has every input for this asset.
- **Readiness** answers "do we have enough history?" A green chip means the asset has cleared the lookback window.

UNAVAILABLE on either means: not yet, but the system is monitoring. Persistent UNAVAILABLE points to a feed issue — investigate from [Ops → Data feeds](/help/reference/pages/ops).

## Avoid the silent biases

- **Survivorship bias** is automatic if you build a universe from "today's index" and run a backtest. The shipped universes are point-in-time and immune to this. Custom universes you build from external sources are flagged "survivorship-unverified" until you verify.
- **Insufficient diversity.** A 50-name universe of one sector is *narrower* than a 10-name universe of independent sectors. The sector-breakdown panel shows this at a glance.
- **Illiquid names** pass universe filters but fail at execution. The default `min ADV` filter excludes them; lowering the filter re-enables them at your own risk.

## See also

- [Universe page](/help/reference/pages/universe) — the page reference.
- [Universe and features](/help/concepts/universe-and-features) — the concept.
