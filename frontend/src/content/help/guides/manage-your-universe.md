---
title: Manage your universe
summary: Create universes, add or remove assets, and check coverage and readiness.
diataxis: how-to
area: guides
updated: 2026-05-23
order: 8
---

Your universe is the list of tradable assets every engine sees. The [Universe page](/help/reference/pages/universe) is where you create, rename, and populate it. Phase 20 shipped the full add/remove flow — before that, the page was read-only and universes were created via the seed script.

## Create a new universe

1. Open [Universe](/help/reference/pages/universe).
2. Click **+ New universe** in the toolbar.
3. Give it a name (must be unique) and an optional description.
4. **Create**.

The new universe lands empty and is selected immediately so you can start adding assets.

## Add an asset

1. Select the universe you want to populate.
2. Click **+ Add asset** above the members chip area.
3. Type a ticker (`AAPL`) or company name (`Apple`); suggestions appear after a short pause.
4. Use ↑/↓ to highlight a row, then Enter to confirm — or click it.

Only assets already ingested by the system are eligible. Tickers that aren't in the assets table can't be added from the UI; have the operator ingest them first.

Assets already in the current universe are filtered out of the suggestion list so you can't accidentally re-add a current member.

## Remove an asset

1. Hover the chip for the ticker you want to remove.
2. Click the **×** that appears.
3. Confirm.

Soft delete — the membership row is preserved with `removed_at = now()`. Backtests covering past dates can still resolve the (universe, asset) tuple via the membership history; the current universe no longer includes it. Re-adding the same ticker later clears `removed_at` instead of inserting a duplicate, so provenance reads as one continuous record.

## Rename a universe

Click **Rename** in the detail card header. The name must be unique across active universes. Memberships are unchanged.

## Deactivate a universe

Click **Deactivate**. The universe disappears from the picker but its membership history stays for replay. You can't deactivate the last active universe — the rest of the product (decision / backtests / RL) needs at least one to target.

There is no hard delete from the UI. If a universe must be permanently removed (very rare — usually you just deactivate), it has to happen at the database layer with operator review.

## Read coverage and readiness

- **Coverage** answers *do we have data?* A green chip means the feature pipeline has every input for this asset.
- **Readiness** answers *do we have enough history?* A green chip means the asset has cleared the lookback window.

UNAVAILABLE on either means: not yet, but the system is monitoring. Persistent UNAVAILABLE points to a feed issue — investigate from [Ops → Data feeds](/help/reference/pages/ops).

## Avoid the silent biases

- **Survivorship bias** is automatic if you build a universe from "today's index" and run a backtest. The shipped universes are point-in-time and immune to this. Custom universes you build from external sources are flagged "survivorship-unverified" until you verify.
- **Insufficient diversity.** A 50-name universe of one sector is *narrower* than a 10-name universe of independent sectors. The sector-breakdown panel shows this at a glance.
- **Illiquid names** pass universe filters but fail at execution. The default `min ADV` filter excludes them; lowering the filter re-enables them at your own risk.

## What this guide deliberately does NOT promise

- **Effective-date scheduling.** "Add this asset on T+1" is not a feature; everything is immediate. Use timing of when *you* click to control when the change takes effect.
- **Bulk import.** Paste-a-list-of-tickers isn't shipped. Add them one at a time.
- **Hard delete.** Deactivation is the supported way to retire a universe; the row stays for audit.

## See also

- [Universe page](/help/reference/pages/universe) — the page reference.
- [Universe and features](/help/concepts/universe-and-features) — the concept.
