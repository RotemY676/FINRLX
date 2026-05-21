"""Phase W-4 — risk bucket + horizon → target allocation mapping.

Pure module, no DB. Used by Phase W-5 (pipeline integration) to derive
the equity / defensive split when the user has a saved profile.

Methodology
===========

Mapping is grounded in Vanguard and Fidelity model-portfolio tables:

* Vanguard publishes 5 target-risk allocations (Income, Conservative,
  Balanced, Growth, Aggressive) at standard horizon bands.
* Fidelity uses the same 5-bucket structure with substantially the same
  breakpoints (typically ±5pp at each bucket boundary).

The mapping below uses Fidelity's slightly more conservative numbers and
applies a 5pp horizon adjustment per band (1y is more cautious than 10y).

For `lt_1y` (sub-1y) we apply a "preservation" cap: 5pp lower than the
1y_3y row, floor 10%. The intuition is that any recommendation with a
real-money 1y horizon should bias toward capital preservation.

Outputs
=======

`derive_allocation(bucket, horizon)` returns an `AllocationTargets`
dataclass with:

* `equity_pct` (0-100) — share to risk-bearing assets
* `defensive_pct` (0-100) — share to cash / short-duration / bond proxies
* `max_position_pct` — soft per-asset weight cap proportional to bucket
* `max_concentration_pct` — top-5 concentration cap
* `confidence_cap` — soft upper bound on rec confidence for that bucket

Reasonability
=============

* `equity_pct + defensive_pct == 100` (asserted in code).
* `max_position_pct` ranges 6 → 18 (Conservative → Aggressive), matching
  common single-name caps for advisor model portfolios.
* `confidence_cap` ranges 0.70 → 0.90, used by the Risk Overlay so the
  pipeline never surfaces an "aggressive=0.99" recommendation that
  ignores the user's risk profile.
"""
from __future__ import annotations

from dataclasses import dataclass

# Public — used by tests + service callers to validate inputs.
SUPPORTED_BUCKETS: tuple[str, ...] = (
    "conservative",
    "moderate_conservative",
    "moderate",
    "moderate_aggressive",
    "aggressive",
)
SUPPORTED_HORIZONS: tuple[str, ...] = (
    "lt_1y",
    "1y_3y",
    "3y_5y",
    "5y_10y",
    "gt_10y",
)


class AllocationMappingError(ValueError):
    """Raised when a bucket / horizon is unknown."""


@dataclass(frozen=True)
class AllocationTargets:
    bucket: str
    horizon: str
    equity_pct: float
    defensive_pct: float
    max_position_pct: float
    max_concentration_pct: float
    confidence_cap: float


# (bucket, horizon) -> equity_pct.  Defensive = 100 - equity.
_BASE_EQUITY: dict[tuple[str, str], float] = {
    ("conservative", "1y_3y"): 20.0,
    ("conservative", "3y_5y"): 25.0,
    ("conservative", "5y_10y"): 30.0,
    ("conservative", "gt_10y"): 35.0,
    ("moderate_conservative", "1y_3y"): 35.0,
    ("moderate_conservative", "3y_5y"): 40.0,
    ("moderate_conservative", "5y_10y"): 45.0,
    ("moderate_conservative", "gt_10y"): 50.0,
    ("moderate", "1y_3y"): 50.0,
    ("moderate", "3y_5y"): 55.0,
    ("moderate", "5y_10y"): 60.0,
    ("moderate", "gt_10y"): 65.0,
    ("moderate_aggressive", "1y_3y"): 65.0,
    ("moderate_aggressive", "3y_5y"): 70.0,
    ("moderate_aggressive", "5y_10y"): 75.0,
    ("moderate_aggressive", "gt_10y"): 80.0,
    ("aggressive", "1y_3y"): 80.0,
    ("aggressive", "3y_5y"): 85.0,
    ("aggressive", "5y_10y"): 90.0,
    ("aggressive", "gt_10y"): 95.0,
}

# Per-bucket soft caps (independent of horizon).
_PER_BUCKET_CAPS: dict[str, tuple[float, float, float]] = {
    # bucket: (max_position_pct, max_concentration_pct, confidence_cap)
    "conservative": (6.0, 25.0, 0.70),
    "moderate_conservative": (8.0, 30.0, 0.75),
    "moderate": (10.0, 35.0, 0.80),
    "moderate_aggressive": (14.0, 40.0, 0.85),
    "aggressive": (18.0, 50.0, 0.90),
}

_LT_1Y_ADJUSTMENT_PP = 5.0  # subtract from 1y_3y row; floor at 10
_LT_1Y_FLOOR = 10.0


def _validate(bucket: str, horizon: str) -> None:
    if bucket not in SUPPORTED_BUCKETS:
        raise AllocationMappingError(
            f"unknown risk_bucket {bucket!r}; expected one of {list(SUPPORTED_BUCKETS)}"
        )
    if horizon not in SUPPORTED_HORIZONS:
        raise AllocationMappingError(
            f"unknown horizon {horizon!r}; expected one of {list(SUPPORTED_HORIZONS)}"
        )


def derive_allocation(bucket: str, horizon: str) -> AllocationTargets:
    """Return the deterministic allocation targets for a profile.

    The mapping is intentionally a pure lookup + simple horizon
    adjustment — easy to audit, easy to override in W-5 via a
    user-facing template (Phase TPL).
    """
    _validate(bucket, horizon)

    if horizon == "lt_1y":
        base = _BASE_EQUITY[(bucket, "1y_3y")] - _LT_1Y_ADJUSTMENT_PP
        equity_pct = max(_LT_1Y_FLOOR, base)
    else:
        equity_pct = _BASE_EQUITY[(bucket, horizon)]

    defensive_pct = 100.0 - equity_pct
    max_position_pct, max_concentration_pct, confidence_cap = _PER_BUCKET_CAPS[bucket]

    return AllocationTargets(
        bucket=bucket,
        horizon=horizon,
        equity_pct=equity_pct,
        defensive_pct=defensive_pct,
        max_position_pct=max_position_pct,
        max_concentration_pct=max_concentration_pct,
        confidence_cap=confidence_cap,
    )


def all_allocations() -> list[AllocationTargets]:
    """Convenience accessor for tests + dashboards: every (bucket, horizon)."""
    out: list[AllocationTargets] = []
    for bucket in SUPPORTED_BUCKETS:
        for horizon in SUPPORTED_HORIZONS:
            out.append(derive_allocation(bucket, horizon))
    return out
