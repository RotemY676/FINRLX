---
title: Export research data
summary: From the Research lab, dump features, prices, or labeled snapshots for offline analysis.
diataxis: how-to
area: guides
updated: 2026-05-22
order: 9
tags: ["admin"]
---

The [Research lab](/help/reference/pages/admin) (admin-only) exposes a dataset export that bundles features, raw prices, and the policy controls in force, so you can analyze them in a local notebook.

## Before you start

You need: the `admin.research` scope (admin or owner). A target date range, the universe you want to export, and a sense of the format you need.

## Steps

1. **Open the Research lab.** Sidebar → OPERATIONS → Research lab.
2. **Scroll to "Dataset Export for Local Research."**
3. **Pick the universe.** The selector lists every universe you can access.
4. **Pick the date range.** Start and end inclusive.
5. **Toggle features.** Include computed features (momentum, volatility, etc.) if you want them alongside raw inputs; turn off if you just need price data.
6. **Pick the format:**
   - **CSV** for spreadsheet inspection — small datasets only.
   - **JSONL** for ML pipelines — recommended for anything > 1M rows; survives memory pressure.
   - **Parquet** for analytical engines (DuckDB, Spark, Pandas) — columnar, compressed.
7. **Click Download.** The bundle is generated server-side; a progress bar tracks it. Large exports may take a minute or two.

## File schema

Every export carries a header row (CSV) or metadata block (JSONL / Parquet) with:

- The universe name and membership snapshot.
- The feature spec used.
- The export timestamp.
- The user identity (you).

This metadata is your audit trail for the export. Re-running an analysis on a stale export against new data gives misleading results — the metadata helps you spot it.

## Where this fits

Use case 1: **Validate a hypothesis offline before requesting a feature in the product.** Pull the data, run your idea in a notebook, decide if it's worth productizing.

Use case 2: **Cross-check the engine's behavior.** Pull features and the corresponding recommendations; verify the engine's outputs are coherent with the inputs.

Use case 3: **Debug a breach.** Pull the full feature snapshot at the moment of the breach; replay locally to see what the engine saw.

## See also

- [Research lab page](/help/reference/pages/admin) — the page reference.
- [Universe and features](/help/concepts/universe-and-features) — what's in the bundle.
