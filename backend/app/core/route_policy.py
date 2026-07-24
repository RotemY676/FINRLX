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
        # ── Anonymous research product (reviewed + accepted 2026-07-23) ──
        # Product decision: a logged-out visitor can research any ticker. These
        # are the surfaces that flow makes: the Simple Mode front door, the
        # Analyst Desk it opens into, and the two lookups they depend on.
        #
        # Accepted because all six are READ-ONLY and per-ticker — they compute
        # research on a symbol the caller names. None exposes tenant state:
        # the platform's own recommendations, portfolios, activity and operator
        # surfaces are gated, deliberately kept out of this set.
        #
        # Residual risk, recorded rather than hidden: dossier/desk builds are
        # unauthenticated compute. Abuse is bounded by the existing per-IP rate
        # limits and the dossier cache, not by identity. Revisit if that stops
        # holding.
        "GET /api/v1/autopilot/dossier",
        "GET /api/v1/autopilot/compare",
        "GET /api/v1/autopilot/desk/{ticker}/status",
        "GET /api/v1/autopilot/desk/{ticker}/{section}",
        "GET /api/v1/assets",
        "GET /api/v1/prices/freshness",
        # ── Public market context (reviewed + accepted 2026-07-24) ──
        # GET /regime is the SPY benchmark's own rule-based regime label,
        # computed from public bars via the identical rule the dossier uses. It
        # takes no user and no db, and returns no tenant state — it is the same
        # class of read-only public market context as the desk it decorates.
        # Added because the anonymous Analyst Desk chrome reads it; keeping it
        # gated made a logged-out desk emit a 401 and fall back to a hardcoded
        # "Risk-on" pill (a fabricated label — zero-fiction violation). Its
        # sibling GET /activity (operator audit trail) stays authenticated via a
        # function-level dependency in api/v1/regime.py.
        "GET /api/v1/regime",
    }
)

# KNOWN P0 SECURITY DEBT (captured 2026-07-21): unauthenticated today, should be
# gated. This set may only shrink. Do NOT add entries to make a new route pass —
# a new unauthenticated route must either be justified in PUBLIC_ALLOWLIST or
# given an auth dependency.
AUTH_DEBT_BASELINE: frozenset[str] = frozenset(
    {
        # EMPTY as of 2026-07-23 — the debt is cleared.
        #
        # 192 routes were recorded here on 2026-07-21. 186 were auth-gated
        # across six increments; the remaining 6 were reviewed and accepted as
        # the anonymous research product, so they moved to PUBLIC_ALLOWLIST
        # above with their rationale rather than being deleted silently.
        #
        # The ratchet still applies and now bites harder: with the set empty,
        # ANY new unauthenticated route is unclassified and fails the audit.
        # Do not add entries here to make a route pass — either justify it in
        # PUBLIC_ALLOWLIST or give it an auth dependency.
        #
        # NOTE: POST /ingest/bars and /ingest/news were auth-gated on 2026-07-21
        # (US-P0-03 enforcement, increment 2) — controlling market-data injection
        # is a zero-fiction control. Removed from the baseline (now require auth).
        # NOTE: the 5 publication governance mutations (stage/approve/publish/
        # defer/suppress) were auth-gated on 2026-07-21 (US-P0-03 enforcement,
        # slice 1) and intentionally removed from this baseline — they now
        # require authentication and are no longer public debt.
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
