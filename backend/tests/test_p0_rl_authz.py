"""US-P0-03 batch 1 — the RL surface refuses anonymous callers.

67 of the 192 audited debt routes lived under /api/v1/rl*: training runs,
artifact import, dataset export and the experiment registry. They mutate models
and consume real compute, so anonymous access was the largest single hole in
the route-authorization audit.

`test_p0_route_authz.py` ratchets the *declared* policy. This file asserts the
*runtime* behaviour, because a shrinking baseline proves nothing on its own —
the entries could have been deleted without anything actually being gated.
"""
from __future__ import annotations

import pytest

from app.core.route_policy import AUTH_DEBT_BASELINE

# One representative per RL module, covering both read and write paths.
ANON_MUST_FAIL = [
    ("get", "/api/v1/rl/agents"),
    ("get", "/api/v1/rl/adapter/status"),
    ("get", "/api/v1/rl/benchmarks"),
    ("get", "/api/v1/rl/finrlx/candidates"),
    ("post", "/api/v1/rl/train"),
    ("post", "/api/v1/rl/finrlx/dataset-export"),
    ("post", "/api/v1/rl/finrlx/research-experiments"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path", ANON_MUST_FAIL)
async def test_rl_routes_reject_anonymous(anon_client, method, path):
    res = await getattr(anon_client, method)(path)
    assert res.status_code == 401, (
        f"{method.upper()} {path} answered {res.status_code} without credentials; "
        "the RL surface must be gated"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path", ANON_MUST_FAIL)
async def test_rl_routes_accept_an_operator_bearer(client, method, path):
    """The gate must not be a blanket denial — a real bearer still gets through."""
    res = await getattr(client, method)(path)
    assert res.status_code != 401, (
        f"{method.upper()} {path} rejected a valid operator bearer"
    )


def test_no_rl_route_remains_in_the_debt_baseline():
    """The baseline is a ratchet: once gated, entries never come back."""
    leftovers = sorted(e for e in AUTH_DEBT_BASELINE if "/api/v1/rl" in e)
    assert leftovers == [], f"RL routes still recorded as auth debt: {leftovers}"
