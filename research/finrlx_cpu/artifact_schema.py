"""FinRL-X research artifact schema.

Defines the JSON structure for local CPU PPO/A2C research artifacts.
All artifacts are research-only, offline-only, shadow-only.
Not eligible for promotion. No production influence.
"""

ARTIFACT_SCHEMA_VERSION = "1.0"

SAFETY_FLAGS = {
    "research_only": True,
    "offline_only": True,
    "shadow_only": True,
    "not_eligible_for_promotion": True,
    "live_pipeline_influence": False,
    "no_broker_execution": True,
    "no_publication_influence": True,
    "no_recommendation_pollution": True,
}

REQUIRED_ARTIFACT_FIELDS = [
    "artifact_type",
    "schema_version",
    "research_only",
    "offline_only",
    "shadow_only",
    "not_eligible_for_promotion",
    "live_pipeline_influence",
    "no_broker_execution",
    "no_publication_influence",
    "no_recommendation_pollution",
    "algorithm",
    "real_neural_training",
    "cpu_only",
    "synthetic_data",
    "dataset_summary",
    "training_config",
    "training_metrics",
    "artifact_created_at",
    "warnings",
]


def build_artifact(
    algorithm: str,
    real_neural_training: bool,
    synthetic_data: bool,
    dataset_summary: dict,
    training_config: dict,
    training_metrics: dict,
    created_at: str,
    warnings: list[str] | None = None,
) -> dict:
    """Build a research artifact dict with all required safety flags."""
    return {
        "artifact_type": "finrlx_cpu_rl_research_artifact",
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        **SAFETY_FLAGS,
        "algorithm": algorithm,
        "real_neural_training": real_neural_training,
        "cpu_only": True,
        "synthetic_data": synthetic_data,
        "dataset_summary": dataset_summary,
        "training_config": training_config,
        "training_metrics": training_metrics,
        "artifact_created_at": created_at,
        "warnings": warnings or [
            "Local CPU research artifact only.",
            "Not eligible for promotion.",
            "Not used by production decisions.",
            "No broker execution.",
        ],
    }


def validate_artifact(artifact: dict) -> tuple[bool, list[str]]:
    """Validate a research artifact has all required fields and safety flags."""
    errors = []
    for field in REQUIRED_ARTIFACT_FIELDS:
        if field not in artifact:
            errors.append(f"Missing required field: {field}")

    if artifact.get("artifact_type") != "finrlx_cpu_rl_research_artifact":
        errors.append(f"Invalid artifact_type: {artifact.get('artifact_type')}")
    if artifact.get("research_only") is not True:
        errors.append("research_only must be true")
    if artifact.get("offline_only") is not True:
        errors.append("offline_only must be true")
    if artifact.get("shadow_only") is not True:
        errors.append("shadow_only must be true")
    if artifact.get("not_eligible_for_promotion") is not True:
        errors.append("not_eligible_for_promotion must be true")
    if artifact.get("live_pipeline_influence") is not False:
        errors.append("live_pipeline_influence must be false")
    if artifact.get("no_broker_execution") is not True:
        errors.append("no_broker_execution must be true")
    if artifact.get("no_publication_influence") is not True:
        errors.append("no_publication_influence must be true")
    if artifact.get("no_recommendation_pollution") is not True:
        errors.append("no_recommendation_pollution must be true")

    return len(errors) == 0, errors
