"""Route authorization policy + audit (US-P0-03).

This module makes the authorization posture of every HTTP route *explicit* and
enforceable. It splits the currently-unauthenticated ("public") routes into two
sets:

* ``PUBLIC_ALLOWLIST`` — endpoints that are **intentionally** unauthenticated
  (health probes, feature flags for the FE boot, the auth entry points). Adding
  a route here is a deliberate, reviewed decision.

* ``AUTH_DEBT_BASELINE`` — endpoints that are unauthenticated **today but should
  not be**. This is recorded, labeled P0 security debt captured on 2026-07-21.
  The audit test enforces a one-way ratchet: this set may only *shrink* (as
  routes get auth-gated) and no *new* unauthenticated route may appear outside
  these two sets. This neither hides the gap (it is fully enumerated and
  surfaced in the runtime-inventory manifest) nor rubber-stamps it as safe.

Entries are keyed as ``"METHOD /path"``. The audit is pure and dependency-free
so it can run in unit tests and feed the operator manifest.
"""
from __future__ import annotations

from collections.abc import Iterable

# Intentionally unauthenticated — reviewed and accepted as public.
PUBLIC_ALLOWLIST: frozenset[str] = frozenset(
    {
        "GET /",
        "GET /health",
        "GET /healthz",
        "GET /api/health",
        "GET /api/v1/health",
        "GET /api/v1/flags",
        "POST /api/v1/auth/login",
        "POST /api/v1/auth/signup",
        "POST /api/v1/auth/refresh",
        "GET /api/v1/auth/google/start",
        "GET /api/v1/auth/google/callback",
    }
)

# KNOWN P0 SECURITY DEBT (captured 2026-07-21): unauthenticated today, should be
# gated. This set may only shrink. Do NOT add entries to make a new route pass —
# a new unauthenticated route must either be justified in PUBLIC_ALLOWLIST or
# given an auth dependency.
AUTH_DEBT_BASELINE: frozenset[str] = frozenset(
    {
        "GET /api/v1/activity",
        "GET /api/v1/analysis/single-ticker",
        "GET /api/v1/assets",
        "GET /api/v1/autopilot/compare",
        "GET /api/v1/autopilot/desk/{ticker}/status",
        "GET /api/v1/autopilot/desk/{ticker}/{section}",
        "GET /api/v1/autopilot/dossier",
        "GET /api/v1/comparison/current",
        "GET /api/v1/engines/comparison",
        "GET /api/v1/engines/definitions",
        "GET /api/v1/engines/disagreement",
        "GET /api/v1/engines/evidence",
        "GET /api/v1/engines/latest-signals",
        "GET /api/v1/engines/runs",
        "GET /api/v1/engines/runs/{run_id}",
        "GET /api/v1/engines/status",
        "GET /api/v1/features/definitions",
        "GET /api/v1/features/latest",
        "GET /api/v1/features/status",
        "GET /api/v1/features/{feature_set_id}",
        "GET /api/v1/ingest/manifests",
        "GET /api/v1/ingest/status",
        "GET /api/v1/news",
        "GET /api/v1/overview",
        "GET /api/v1/pipeline/latest",
        "GET /api/v1/pipeline/runs",
        "GET /api/v1/pipeline/runs/{recommendation_id}",
        "GET /api/v1/pipeline/status",
        "GET /api/v1/pricechart",
        "GET /api/v1/prices/freshness",
        "GET /api/v1/recommendations/current",
        "GET /api/v1/recommendations/{recommendation_id}",
        "GET /api/v1/recommendations/{recommendation_id}/stages",
        "GET /api/v1/regime",
        "GET /api/v1/scenario/baseline",
        "POST /api/v1/engines/run",
        "POST /api/v1/features/compute",
        # NOTE: POST /ingest/bars and /ingest/news were auth-gated on 2026-07-21
        # (US-P0-03 enforcement, increment 2) — controlling market-data injection
        # is a zero-fiction control. Removed from the baseline (now require auth).
        "POST /api/v1/pipeline/run",
        # NOTE: the 5 publication governance mutations (stage/approve/publish/
        # defer/suppress) were auth-gated on 2026-07-21 (US-P0-03 enforcement,
        # slice 1) and intentionally removed from this baseline — they now
        # require authentication and are no longer public debt.
        "POST /api/v1/scenario/simulate",
    }
)


def classify_public_routes(public_entries: Iterable[str]) -> dict[str, list[str]]:
    """Split currently-public routes into allowed / known-debt / unclassified.

    ``unclassified`` is the enforcement signal: it must always be empty. A
    non-empty result means a route is unauthenticated without being either an
    accepted public endpoint or previously-recorded debt — i.e. a new exposure
    that must be triaged before merge.
    """
    entries = set(public_entries)
    return {
        "allowed": sorted(entries & PUBLIC_ALLOWLIST),
        "debt": sorted(entries & AUTH_DEBT_BASELINE),
        "unclassified": sorted(entries - PUBLIC_ALLOWLIST - AUTH_DEBT_BASELINE),
    }
