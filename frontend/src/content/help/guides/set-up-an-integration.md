---
title: Set up an integration
summary: Connect a market-data or fundamentals source from the Integrations page.
diataxis: how-to
area: guides
updated: 2026-05-22
order: 10
---

Integrations are how FINRLX pulls external data. The [Integrations page](/help/reference/pages/integrations) groups them by category and surfaces per-connection status.

## Steps

1. **Open Integrations.** Sidebar → OPERATIONS → Integrations.
2. **Find the integration you want.** They are grouped by category: Fundamentals, Market Data, News.
3. **Click the integration card.** A detail panel opens with description, data contributed, and the credentials state.
4. **Enter credentials** (where required). Most market-data sources require an API key; some are centrally managed and do not.
5. **Click "Test connection."** A synthetic fetch confirms the integration works end-to-end. A green status chip means you are done.
6. **Click "Enable."** The integration is now feeding the data pipeline.

## After enabling

The integration's data takes one cycle to flow through to recommendations. Within that cycle:

- **Coverage chips** on the [Universe page](/help/reference/pages/universe) should improve if the new integration brings missing data.
- **Confidence floors** may clear if the new integration unblocks a stuck `data` confidence check.

Check the per-integration **Last fetch** timestamp to confirm fresh data is arriving.

## Troubleshooting

### Test connection fails

- Confirm the API key is correct and active on the source.
- Confirm your network can reach the source (some integrations have IP allowlists on the source side).
- Read the error detail in the test result — the message identifies the failing step.

### Connection works but no data arrives

- The integration may be rate-limited. Check the source's quota dashboard.
- The integration may have credentials with insufficient scope. Re-issue credentials with full read access.
- The integration's source may be experiencing an outage on its side.

## See also

- [Integrations page](/help/reference/pages/integrations) — the page reference.
- [Universe and features](/help/concepts/universe-and-features) — how integration data enters the engine.
