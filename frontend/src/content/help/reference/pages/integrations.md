---
title: Integrations
summary: External data sources grouped by category, with per-connection status.
diataxis: reference
area: reference
updated: 2026-05-22
order: 111
---

The Integrations page groups every external connection by category and surfaces per-connection status.

## Categories

### Fundamentals

Sources for fundamental data: earnings, balance-sheet metrics, valuation ratios. Connected sources contribute their data to the feature pipeline with appropriate availability-date stamping. See [Universe and features](/help/concepts/universe-and-features#features).

### Market data

Sources for price and volume data. Multiple sources can be enabled simultaneously; the data layer reconciles them and exposes a unified canonical price series. UNAVAILABLE on a market-data source is the most consequential operational issue.

### News

External news links surfaced on the [News page](/help/reference/pages/news).

## Per-integration status

Every integration card shows:

- **Connection chip** — OK / WARN / UNAVAILABLE.
- **Last fetch** — timestamp of the most recent successful pull.
- **Lag** — time since last fetch vs. the configured SLA.
- **Credentials state** — whether the integration requires API keys and whether they are valid.

## Actions

- **Test connection** — runs a synthetic fetch and reports status.
- **Refresh credentials** — re-enters API keys (where applicable).
- **Enable / Disable** — toggles inclusion in the data pipeline.

## See also

- [Set up an integration](/help/guides/set-up-an-integration) — the how-to.
