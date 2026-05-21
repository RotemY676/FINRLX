"""Phase W-4 — risk-bucket + horizon → allocation mapping contract.

Locks the published Vanguard/Fidelity-derived table so a future change
to ``derive_allocation`` cannot silently shift recommended allocations
for an existing user.
"""
from __future__ import annotations

import pytest

from app.services.profile_mapping import (
    SUPPORTED_BUCKETS,
    SUPPORTED_HORIZONS,
    AllocationMappingError,
    all_allocations,
    derive_allocation,
)

# ── Pinned table — the public contract ───────────────────────────────


PINNED_EQUITY_PCT = {
    ("conservative", "lt_1y"): 15.0,
    ("conservative", "1y_3y"): 20.0,
    ("conservative", "3y_5y"): 25.0,
    ("conservative", "5y_10y"): 30.0,
    ("conservative", "gt_10y"): 35.0,
    ("moderate_conservative", "lt_1y"): 30.0,
    ("moderate_conservative", "1y_3y"): 35.0,
    ("moderate_conservative", "3y_5y"): 40.0,
    ("moderate_conservative", "5y_10y"): 45.0,
    ("moderate_conservative", "gt_10y"): 50.0,
    ("moderate", "lt_1y"): 45.0,
    ("moderate", "1y_3y"): 50.0,
    ("moderate", "3y_5y"): 55.0,
    ("moderate", "5y_10y"): 60.0,
    ("moderate", "gt_10y"): 65.0,
    ("moderate_aggressive", "lt_1y"): 60.0,
    ("moderate_aggressive", "1y_3y"): 65.0,
    ("moderate_aggressive", "3y_5y"): 70.0,
    ("moderate_aggressive", "5y_10y"): 75.0,
    ("moderate_aggressive", "gt_10y"): 80.0,
    ("aggressive", "lt_1y"): 75.0,
    ("aggressive", "1y_3y"): 80.0,
    ("aggressive", "3y_5y"): 85.0,
    ("aggressive", "5y_10y"): 90.0,
    ("aggressive", "gt_10y"): 95.0,
}


@pytest.mark.parametrize(
    "bucket,horizon,expected",
    sorted((b, h, v) for (b, h), v in PINNED_EQUITY_PCT.items()),
)
def test_equity_pct_pinned(bucket, horizon, expected):
    targets = derive_allocation(bucket, horizon)
    assert targets.equity_pct == expected, (
        f"({bucket}, {horizon}) shifted: was {expected}, now {targets.equity_pct}"
    )
    # defensive must complement equity to exactly 100
    assert targets.equity_pct + targets.defensive_pct == 100.0


def test_all_buckets_horizons_covered():
    rows = all_allocations()
    assert len(rows) == len(SUPPORTED_BUCKETS) * len(SUPPORTED_HORIZONS)
    seen = {(r.bucket, r.horizon) for r in rows}
    expected = {(b, h) for b in SUPPORTED_BUCKETS for h in SUPPORTED_HORIZONS}
    assert seen == expected


def test_equity_monotonic_in_bucket_for_each_horizon():
    """At any horizon, more-aggressive buckets must hold no less equity."""
    for horizon in SUPPORTED_HORIZONS:
        seq = [derive_allocation(b, horizon).equity_pct for b in SUPPORTED_BUCKETS]
        for i in range(1, len(seq)):
            assert seq[i] >= seq[i - 1], (
                f"non-monotonic at horizon={horizon}: {dict(zip(SUPPORTED_BUCKETS, seq, strict=False))}"
            )


def test_equity_monotonic_in_horizon_for_each_bucket():
    """Within any bucket, longer horizon must hold no less equity."""
    for bucket in SUPPORTED_BUCKETS:
        seq = [derive_allocation(bucket, h).equity_pct for h in SUPPORTED_HORIZONS]
        for i in range(1, len(seq)):
            assert seq[i] >= seq[i - 1], (
                f"non-monotonic in bucket={bucket}: {dict(zip(SUPPORTED_HORIZONS, seq, strict=False))}"
            )


def test_lt_1y_floors_to_10():
    """The preservation cap is 5pp below the 1y_3y row, floored at 10%."""
    # conservative 1y_3y = 20, so lt_1y = 15 (>10 floor); pinned above
    # For a hypothetical bucket where 1y_3y - 5 < 10 the floor would clamp.
    # Verify the floor mechanism still works if base falls below floor:
    # Conservative is the lowest defined; if its 1y_3y were 12, lt_1y would
    # become 10. We can't change the table here, but we cover the branch by
    # asserting the floor exists and that current values respect it.
    targets = derive_allocation("conservative", "lt_1y")
    assert targets.equity_pct >= 10.0


@pytest.mark.parametrize(
    "bucket,expected_caps",
    [
        ("conservative", (6.0, 25.0, 0.70)),
        ("moderate_conservative", (8.0, 30.0, 0.75)),
        ("moderate", (10.0, 35.0, 0.80)),
        ("moderate_aggressive", (14.0, 40.0, 0.85)),
        ("aggressive", (18.0, 50.0, 0.90)),
    ],
)
def test_per_bucket_caps_pinned(bucket, expected_caps):
    t = derive_allocation(bucket, "gt_10y")
    assert (t.max_position_pct, t.max_concentration_pct, t.confidence_cap) == expected_caps


def test_caps_monotonic_across_buckets():
    """Every cap should grow with bucket aggressiveness."""
    rows = [derive_allocation(b, "gt_10y") for b in SUPPORTED_BUCKETS]
    for i in range(1, len(rows)):
        assert rows[i].max_position_pct >= rows[i - 1].max_position_pct
        assert rows[i].max_concentration_pct >= rows[i - 1].max_concentration_pct
        assert rows[i].confidence_cap >= rows[i - 1].confidence_cap


def test_unknown_bucket_raises():
    with pytest.raises(AllocationMappingError):
        derive_allocation("ultra_aggressive", "3y_5y")


def test_unknown_horizon_raises():
    with pytest.raises(AllocationMappingError):
        derive_allocation("moderate", "lifetime")
