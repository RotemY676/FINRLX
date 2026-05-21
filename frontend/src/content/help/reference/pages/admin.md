---
title: Research lab (admin)
summary: Research data browser and dataset export for offline analysis.
diataxis: reference
area: reference
updated: 2026-05-22
order: 113
tags: ["admin"]
---

The Research lab is an admin-only screen for browsing research data and exporting datasets for offline analysis.

## Sections

### Research data browser

A tabular view of feature vectors, price series, and labeled snapshots for any universe in any time window. Filterable by asset, date range, and feature set.

### Dataset export for local research

The export form bundles data into a downloadable file. Fields:

- **Date range** — start and end dates for the export.
- **Universe** — the universe whose membership defines the asset list.
- **Feature toggles** — include / exclude price features, technical indicators, fundamentals.
- **Format** — CSV, JSONL, or Parquet. JSONL is recommended for large datasets.
- **Include computed features** — when on, the export includes momentum, volatility, and other engineered features alongside raw inputs.

## Permissions

The page renders only for users with the `admin.research` scope. Without that scope, the route redirects.

## Output format notes

- **CSV** — one row per (asset, date), one column per feature. Good for spreadsheet inspection.
- **JSONL** — one JSON object per line. Survives large datasets without loading everything in memory. Recommended for downstream ML pipelines.
- **Parquet** — columnar, compressed. Best for analytical query engines (DuckDB, Spark, Pandas).

## See also

- [Export research data](/help/guides/export-research-data) — the how-to.
