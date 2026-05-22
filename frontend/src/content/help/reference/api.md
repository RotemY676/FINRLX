---
title: REST API
summary: The /api/v1/* endpoints used by the workspace — methods, payloads, auth.
diataxis: reference
area: reference
updated: 2026-05-22
order: 4
---

The FINRLX backend exposes a REST surface under `/api/v1/`. The workspace itself is a consumer of this API; everything visible in the UI is reachable from a script with the right credentials. This page is the catalog of endpoints grouped by area.

## Authentication

All endpoints require a bearer token in the `Authorization` header. Obtain a token by completing OAuth on `/login` and reading the `Authorization` header from the response. Tokens expire; refresh tokens are issued alongside.

```
Authorization: Bearer <token>
```

Requests without a valid token return `401 Unauthorized`. Requests with a token that lacks the required scope for an endpoint return `403 Forbidden`.

## Profile

### `GET /api/v1/profile/questions`

Returns the catalog of wizard questions, organized by dimension.

```jsonc
{
  "version": "2026-05-22",
  "dimensions": [
    {
      "id": "knowledge",
      "questions": [ /* … */ ]
    }
    /* … */
  ]
}
```

### `GET /api/v1/profile/me`

Returns the current user's profile, including derived defaults.

```jsonc
{
  "user_id": "...",
  "has_profile": true,
  "risk_profile": "balanced",
  "default_universe": "us_large_cap",
  "default_horizon": "1M",
  "wizard_version": "2026-05-22",
  "submitted_at": "2026-05-12T10:14:00Z"
}
```

### `POST /api/v1/profile`

Submits a complete set of wizard answers. The server derives `risk_profile`, `default_universe`, and `default_horizon` from the answers.

```jsonc
{
  "answers": {
    "knowledge.experience_years": 3,
    "risk.max_drawdown_tolerance": "moderate",
    /* … */
  }
}
```

Returns the new profile object identical in shape to the response from `GET /profile/me`.

## Recommendations

### `GET /api/v1/recommendations`

Returns the current published recommendation stream for the authenticated user.

Query parameters:

- `limit` — int, default 20, max 100.
- `before` — ISO timestamp; returns recommendations issued before this moment.

```jsonc
{
  "items": [
    {
      "id": "rec_...",
      "issued_at": "2026-05-22T14:00:00Z",
      "engine": "ensemble",
      "weights": [{ "symbol": "AAPL", "weight": 0.28 }, /* … */],
      "status": "published",
      "evidence_id": "ev_..."
    }
  ],
  "next_cursor": null
}
```

## Backtests

### `GET /api/v1/backtests`

Lists backtest experiments.

### `GET /api/v1/backtests/{id}`

Returns a single experiment with its configuration, equity curve, metrics, and provenance.

### `POST /api/v1/backtests`

Creates a new experiment. Body specifies the universe, engine, feature spec, date range, cost model, and benchmarks.

## Policies

### `GET /api/v1/policies`

Returns the active policy bundle (every named control with its current value).

### `PATCH /api/v1/policies`

Edits one or more controls. Body is partial — only changed controls need to be present.

```jsonc
{
  "CASH_FLOOR": 0.10,
  "reason": "Tightening for late-cycle regime"
}
```

The patch is versioned in the audit trail with the supplied reason.

### `GET /api/v1/policies/breaches`

Lists active and recent breaches.

## Universe

### `GET /api/v1/universe`

Lists all universes available to the authenticated user.

### `GET /api/v1/universe/{id}`

Returns one universe with point-in-time membership intervals, coverage status, and readiness flags.

### `POST /api/v1/universe`

Creates a custom universe. Requires the `universe.create` scope.

## Workspace

### `GET /api/v1/workspace/counts`

Returns sidebar badge counts (active breaches, queued decisions, etc.).

### `GET /api/v1/workspace/saved-views`

Returns the user's saved comparison views and dashboard layouts.

## Research documents (Phase 17)

### `POST /api/v1/research/documents`

Upload a PDF against a ticker. `multipart/form-data` body with `ticker` and `file` parts. Returns the persisted document with extracted-text metadata.

### `GET /api/v1/research/documents?ticker=NVDA`

List documents for a ticker (newest first). Shared by ticker — any signed-in user can read.

### `GET /api/v1/research/documents/{id}`

Single document with full extracted text body.

### `POST /api/v1/research/documents/{id}/analyze`

Ask an LLM question grounded in the document. JSON body: `{"prompt": "..."}`. Returns the answer with provider/model/token provenance. 503 when no LLM provider is configured or the monthly budget would be exceeded.

### `GET /api/v1/research/documents/_usage`

Monthly LLM token-budget status: used / cap / remaining + per-provider breakdown.

## Research insights + SEC EDGAR (Phase 18)

### `POST /api/v1/research/{ticker}/auto-ingest`

Fetch the last 6 quarterly filings (10-Q + 10-K) from SEC EDGAR, download, extract text, and persist as `research_documents` rows with `source="sec_auto"`. Idempotent — re-running for the same ticker dedups via the `(ticker, sec_accession_no)` unique index. Returns counts:

```jsonc
{
  "ticker": "NVDA",
  "cik": "0001045810",
  "ingested": 2,
  "skipped_existing": 4,
  "failed": 0,
  "failures": [],
  "document_ids": [ "...", "..." ]
}
```

- `404` when the ticker is not in SEC's table (non-US listing).
- `503` when `SEC_USER_AGENT` env var is empty or SEC is unreachable.

### `POST /api/v1/research/{ticker}/insights`

Synthesize cross-quarter insights across the ticker's sec_auto documents. Returns the persisted `TickerInsights` row with `summary_text` (markdown), `quarters_covered` (list of accession numbers), provider/model/token provenance.

- `409` when no sec_auto documents are ready (call `/auto-ingest` first).
- `503` when the LLM provider chain is exhausted or the monthly token budget would be exceeded.

### `GET /api/v1/research/{ticker}/insights`

Most recent `TickerInsights` row for the ticker, or `data: null` if none generated yet. The FE checks `generated_at` against a 7-day TTL to decide whether to offer a refresh.

### `GET /api/v1/research/edgar/probe?ticker=NVDA&limit=6`

Diagnostic endpoint: resolve a ticker to a CIK and list its recent quarterly filings without persisting anything. Useful for verifying `SEC_USER_AGENT` is correctly set on a new deploy.

## Errors

All endpoints use standard HTTP status codes and a uniform error body:

```jsonc
{
  "error": {
    "code": "policy_validation_failed",
    "message": "CASH_FLOOR must be between 0 and 0.5",
    "details": { "field": "CASH_FLOOR", "value": 0.7 }
  }
}
```

`4xx` codes indicate client errors; `5xx` codes indicate server errors and should be retried with backoff.

## Versioning

The API surface is versioned in the URL (`/api/v1/`). Breaking changes ship as `/api/v2/...` with the prior version supported in parallel for at least one full deprecation cycle. Non-breaking additions (new optional fields, new endpoints) ship into the existing version.

## See also

- [Integrations](/help/reference/pages/integrations) — for external data sources that consume or feed the API.
- [Governance and audit](/help/concepts/governance-and-audit) — every mutating API call is audit-logged.
