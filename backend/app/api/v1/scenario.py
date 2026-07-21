"""Scenario simulation endpoint.

POST /api/v1/scenario/simulate — run a what-if scenario with modified parameters.

The simulation is a simplified model: it computes deltas based on parameter
deviations from the baseline. A real implementation would run the full
engine pipeline with modified inputs.
"""

from fastapi import APIRouter

from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.schemas.scenario import ScenarioDelta, ScenarioParams, ScenarioResult

router = APIRouter()

# Baseline values matching the design handoff
BASELINE = ScenarioParams()
BASELINE_WEIGHT = 4.2
BASELINE_CONFIDENCE = 0.74
BASELINE_EXPECTED_RETURN = 6.4


def _simulate(params: ScenarioParams) -> ScenarioResult:
    """Simplified scenario simulation engine.

    Computes delta impacts based on how far each parameter deviates
    from baseline. This is a linear approximation — a real engine
    would re-run the full pipeline.
    """
    is_modified = params != BASELINE

    if not is_modified:
        return ScenarioResult(
            is_modified=False,
            deltas=[],
            weight_impact=0.0,
            confidence_impact=0.0,
            expected_return_impact=0.0,
        )

    # Impact factors (sensitivity coefficients)
    weight_delta = 0.0
    conf_delta = 0.0
    return_delta = 0.0
    warnings: list[str] = []

    # Horizon impact: shorter = less confident, longer = more smoothing
    horizon_diff = params.horizon_days - BASELINE.horizon_days
    conf_delta += horizon_diff * 0.0005  # +0.05 per 100 days
    return_delta += horizon_diff * 0.02  # +2% per 100 days

    # Rate shock impact
    if params.rate_shock_bps != 0:
        weight_delta -= abs(params.rate_shock_bps) * 0.002  # -0.2% per 100bps
        conf_delta -= abs(params.rate_shock_bps) * 0.0003
        return_delta -= params.rate_shock_bps * 0.008  # directional
        if abs(params.rate_shock_bps) > 100:
            warnings.append(f"Rate shock {params.rate_shock_bps}bps exceeds historical 1σ range")

    # Correlation impact
    corr_diff = params.correlation - BASELINE.correlation
    weight_delta -= corr_diff * 2.0  # higher corr = lower weight allocation
    conf_delta -= corr_diff * 0.1

    # Earnings revision weight
    erw_diff = params.earnings_revision_weight - BASELINE.earnings_revision_weight
    return_delta += erw_diff * 3.0  # earnings are a strong return driver

    # Engine toggles
    if not params.momentum_engine_on:
        conf_delta -= 0.04
        return_delta -= 1.2
        warnings.append("Momentum engine disabled — removes strongest signal contributor")
    if params.flow_engine_on:
        conf_delta += 0.02
        weight_delta -= 0.3  # flow is currently bearish, reduces weight
    if not params.policy_constraints_on:
        weight_delta += 0.8  # removing constraints allows higher allocation
        warnings.append("Policy constraints disabled — position may exceed limits")

    # Clamp impacts
    weight_delta = max(-BASELINE_WEIGHT, min(weight_delta, 3.0))
    conf_delta = max(-0.3, min(conf_delta, 0.15))
    return_delta = max(-10.0, min(return_delta, 10.0))

    new_weight = round(BASELINE_WEIGHT + weight_delta, 1)
    new_conf = round(BASELINE_CONFIDENCE + conf_delta, 2)
    new_return = round(BASELINE_EXPECTED_RETURN + return_delta, 1)

    deltas = [
        ScenarioDelta(
            metric="Weight",
            baseline=f"{BASELINE_WEIGHT}%",
            modified=f"{new_weight}%",
            direction="neg" if weight_delta < -0.1 else "pos" if weight_delta > 0.1 else "neutral",
        ),
        ScenarioDelta(
            metric="Confidence",
            baseline=f"{BASELINE_CONFIDENCE}",
            modified=f"{new_conf}",
            direction="neg" if conf_delta < -0.02 else "pos" if conf_delta > 0.02 else "neutral",
        ),
        ScenarioDelta(
            metric="Expected Δ",
            baseline=f"+{BASELINE_EXPECTED_RETURN}%",
            modified=f"{'+' if new_return > 0 else ''}{new_return}%",
            direction="neg" if return_delta < -0.5 else "pos" if return_delta > 0.5 else "neutral",
        ),
    ]

    return ScenarioResult(
        is_modified=True,
        deltas=deltas,
        weight_impact=round(weight_delta, 2),
        confidence_impact=round(conf_delta, 3),
        expected_return_impact=round(return_delta, 2),
        warnings=warnings,
    )


@router.post("/scenario/simulate", response_model=ApiResponse[ScenarioResult])
async def simulate_scenario(params: ScenarioParams):
    result = _simulate(params)
    return ApiResponse(
        meta=make_meta(warnings=result.warnings, is_demo=True), data=result
    )


@router.get("/scenario/baseline", response_model=ApiResponse[ScenarioParams])
async def get_baseline():
    """Return the baseline scenario parameters."""
    return ApiResponse(meta=make_meta(is_demo=True), data=BASELINE)
