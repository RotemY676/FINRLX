"""Tests for research artifact schema validation.

These tests do NOT require torch/gymnasium/stable-baselines3.
They validate the artifact schema and safety flags only.

Run: python -m pytest research/finrlx_cpu/tests/ -v
"""

import sys
import os

# Add parent to path so we can import artifact_schema
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from artifact_schema import build_artifact, validate_artifact, SAFETY_FLAGS, REQUIRED_ARTIFACT_FIELDS


def test_build_artifact_has_all_required_fields():
    artifact = build_artifact(
        algorithm="PPO",
        real_neural_training=True,
        synthetic_data=True,
        dataset_summary={"row_count": 60, "synthetic": True},
        training_config={"algorithm": "PPO", "timesteps": 200, "seed": 42},
        training_metrics={"total_reward": 0.01, "training_duration_ms": 500},
        created_at="2026-04-26T12:00:00Z",
    )
    for field in REQUIRED_ARTIFACT_FIELDS:
        assert field in artifact, f"Missing field: {field}"


def test_artifact_marks_research_only():
    artifact = build_artifact(
        algorithm="A2C",
        real_neural_training=True,
        synthetic_data=False,
        dataset_summary={},
        training_config={},
        training_metrics={},
        created_at="2026-04-26T12:00:00Z",
    )
    assert artifact["research_only"] is True
    assert artifact["offline_only"] is True
    assert artifact["shadow_only"] is True


def test_artifact_not_eligible_for_promotion():
    artifact = build_artifact(
        algorithm="PPO",
        real_neural_training=True,
        synthetic_data=True,
        dataset_summary={},
        training_config={},
        training_metrics={},
        created_at="2026-04-26T12:00:00Z",
    )
    assert artifact["not_eligible_for_promotion"] is True
    assert artifact["live_pipeline_influence"] is False
    assert artifact["no_broker_execution"] is True
    assert artifact["no_publication_influence"] is True
    assert artifact["no_recommendation_pollution"] is True


def test_artifact_cannot_be_confused_with_production():
    artifact = build_artifact(
        algorithm="PPO",
        real_neural_training=True,
        synthetic_data=True,
        dataset_summary={},
        training_config={},
        training_metrics={},
        created_at="2026-04-26T12:00:00Z",
    )
    assert artifact["artifact_type"] == "finrlx_cpu_rl_research_artifact"
    assert artifact["no_broker_execution"] is True
    assert artifact["live_pipeline_influence"] is False


def test_synthetic_data_labeled():
    artifact = build_artifact(
        algorithm="PPO",
        real_neural_training=True,
        synthetic_data=True,
        dataset_summary={"synthetic": True},
        training_config={},
        training_metrics={},
        created_at="2026-04-26T12:00:00Z",
        warnings=["Trained on SYNTHETIC data."],
    )
    assert artifact["synthetic_data"] is True


def test_real_data_labeled():
    artifact = build_artifact(
        algorithm="PPO",
        real_neural_training=True,
        synthetic_data=False,
        dataset_summary={"synthetic": False, "source": "exported.json"},
        training_config={},
        training_metrics={},
        created_at="2026-04-26T12:00:00Z",
    )
    assert artifact["synthetic_data"] is False


def test_validate_artifact_passes_valid():
    artifact = build_artifact(
        algorithm="PPO",
        real_neural_training=True,
        synthetic_data=True,
        dataset_summary={},
        training_config={},
        training_metrics={},
        created_at="2026-04-26T12:00:00Z",
    )
    valid, errors = validate_artifact(artifact)
    assert valid is True
    assert errors == []


def test_validate_artifact_rejects_missing_field():
    artifact = build_artifact(
        algorithm="PPO",
        real_neural_training=True,
        synthetic_data=True,
        dataset_summary={},
        training_config={},
        training_metrics={},
        created_at="2026-04-26T12:00:00Z",
    )
    del artifact["research_only"]
    valid, errors = validate_artifact(artifact)
    assert valid is False
    assert any("research_only" in e for e in errors)


def test_validate_artifact_rejects_wrong_type():
    artifact = build_artifact(
        algorithm="PPO",
        real_neural_training=True,
        synthetic_data=True,
        dataset_summary={},
        training_config={},
        training_metrics={},
        created_at="2026-04-26T12:00:00Z",
    )
    artifact["artifact_type"] = "production_policy"
    valid, errors = validate_artifact(artifact)
    assert valid is False


def test_validate_artifact_rejects_unsafe_flags():
    artifact = build_artifact(
        algorithm="PPO",
        real_neural_training=True,
        synthetic_data=True,
        dataset_summary={},
        training_config={},
        training_metrics={},
        created_at="2026-04-26T12:00:00Z",
    )
    artifact["no_broker_execution"] = False
    valid, errors = validate_artifact(artifact)
    assert valid is False
    assert any("no_broker_execution" in e for e in errors)


def test_safety_flags_are_correct():
    assert SAFETY_FLAGS["research_only"] is True
    assert SAFETY_FLAGS["offline_only"] is True
    assert SAFETY_FLAGS["shadow_only"] is True
    assert SAFETY_FLAGS["not_eligible_for_promotion"] is True
    assert SAFETY_FLAGS["live_pipeline_influence"] is False
    assert SAFETY_FLAGS["no_broker_execution"] is True
    assert SAFETY_FLAGS["no_publication_influence"] is True
    assert SAFETY_FLAGS["no_recommendation_pollution"] is True
