"""US-P0-03 — route authorization matrix + one-way ratchet.

Every HTTP route is either authenticated, on the intentionally-public allowlist,
or in the recorded (labeled) auth-debt baseline. The core invariant is that the
`unclassified` bucket is empty: a NEW unauthenticated route cannot be merged
without being explicitly triaged. The baseline may only shrink, never grow.
"""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi.routing import APIRoute

from app.core.config import settings
from app.core.route_policy import (
    AUTH_DEBT_BASELINE,
    PUBLIC_ALLOWLIST,
    classify_public_routes,
)
from app.main import app
from app.services.runtime_inventory import build_runtime_inventory


def _all_route_entries() -> set[str]:
    entries: set[str] = set()
    for r in app.routes:
        if isinstance(r, APIRoute):
            for m in (r.methods or set()):
                if m not in {"HEAD", "OPTIONS"}:
                    entries.add(f"{m} {r.path}")
    return entries


def _public_entries() -> list[str]:
    inv = build_runtime_inventory(app=app, settings=settings, now=datetime.now(UTC))
    return [f"{m} {ri.path}" for ri in inv.routes if ri.auth == "public" for m in ri.methods]


def test_no_unclassified_public_route():
    """The enforcement gate: no unauthenticated route outside allowlist+debt.

    If this fails, a route was added (or lost its auth dependency) without being
    triaged. Fix it by adding an auth dependency, or — only if it is genuinely
    meant to be public — add it to PUBLIC_ALLOWLIST with justification.
    """
    split = classify_public_routes(_public_entries())
    assert split["unclassified"] == [], (
        "Unauthenticated routes not triaged: " + ", ".join(split["unclassified"])
    )


def test_allowlist_and_debt_are_disjoint():
    assert PUBLIC_ALLOWLIST.isdisjoint(AUTH_DEBT_BASELINE)


def test_policy_has_no_stale_entries():
    """Every allowlist/debt entry must reference a route that still exists.

    Prevents the policy from rotting when routes are renamed or removed. A route
    that gets auth-gated simply drops out of the public set — which is allowed
    and desired — but it must still exist somewhere in the app.
    """
    all_entries = _all_route_entries()
    stale_allow = sorted(PUBLIC_ALLOWLIST - all_entries)
    stale_debt = sorted(AUTH_DEBT_BASELINE - all_entries)
    assert stale_allow == [], f"stale PUBLIC_ALLOWLIST entries: {stale_allow}"
    assert stale_debt == [], f"stale AUTH_DEBT_BASELINE entries: {stale_debt}"


def test_baseline_entries_are_still_public():
    """Every debt-baseline entry must still be unauthenticated (public).

    Once a route is auth-gated it MUST be removed from AUTH_DEBT_BASELINE — the
    ledger may not carry a now-authenticated route as if it were open debt. This
    invariant keeps the debt count honest and forces removal-on-gating. (Added
    after the council caught a gated route left stale in the baseline.)
    """
    public = set(_public_entries())
    now_authenticated = sorted(AUTH_DEBT_BASELINE - public)
    assert now_authenticated == [], (
        "these routes are authenticated but still in AUTH_DEBT_BASELINE (remove them): "
        + ", ".join(now_authenticated)
    )


def test_debt_only_shrinks():
    """The set of currently-public debt routes must be a subset of the baseline.

    New unauthenticated exposure cannot hide inside the debt bucket.
    """
    split = classify_public_routes(_public_entries())
    assert set(split["debt"]) <= AUTH_DEBT_BASELINE


def test_manifest_surfaces_authz_audit():
    inv = build_runtime_inventory(app=app, settings=settings, now=datetime.now(UTC))
    assert set(inv.authz.keys()) == {"allowed", "debt", "unclassified"}
    assert inv.authz["unclassified"] == 0
    assert inv.authz["allowed"] >= 1
    # The manifest count and the enumerated list agree.
    assert inv.authz["unclassified"] == len(inv.unclassified_public_routes)
