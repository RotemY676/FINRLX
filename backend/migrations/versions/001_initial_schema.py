"""Initial schema: 18 tables covering all data domains.

Revision ID: 001_initial
Revises: None
Create Date: 2026-04-24

Domains (per Data Model doc 11):
  1. Reference Data: assets, universes, universe_memberships, benchmarks
  4. Signals: signal_runs, signal_outputs
  5. Decision Pipeline: selection_runs, allocation_results, timing_results, risk_overlay_results
  6. Recommendation: recommendations, recommendation_weights
  7. Validation: backtest_experiments, paper_portfolios, replay_snapshots
  8. Admin/Ops: audit_events, incidents, system_health_snapshots
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === Domain 1: Reference Data ===
    op.create_table(
        "assets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("ticker", sa.String(20), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("asset_type", sa.String(50), nullable=False, server_default="equity"),
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column("exchange", sa.String(50), nullable=True),
        sa.Column("currency", sa.String(10), server_default="USD"),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "universes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "universe_memberships",
        sa.Column("universe_id", sa.String(36), primary_key=True),
        sa.Column("asset_id", sa.String(36), primary_key=True),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "benchmarks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("ticker", sa.String(20), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # === Domain 6: Recommendations ===
    op.create_table(
        "recommendations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("universe_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("model_confidence", sa.Float, nullable=True),
        sa.Column("data_confidence", sa.Float, nullable=True),
        sa.Column("operational_confidence", sa.Float, nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rationale_summary", sa.Text, nullable=True),
        sa.Column("warnings", sa.JSON, nullable=True),
        sa.Column("policy_version_id", sa.String(36), nullable=True),
        sa.Column("data_as_of", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "recommendation_weights",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("recommendation_id", sa.String(36), nullable=False, index=True),
        sa.Column("asset_id", sa.String(36), nullable=False),
        sa.Column("target_weight", sa.Float, nullable=False),
        sa.Column("previous_weight", sa.Float, nullable=True),
        sa.Column("delta", sa.Float, nullable=True),
        sa.Column("stance", sa.String(30), nullable=True),
        sa.Column("rationale", sa.Text, nullable=True),
    )

    # === Domain 5: Decision Pipeline ===
    op.create_table(
        "selection_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("recommendation_id", sa.String(36), nullable=False, index=True),
        sa.Column("universe_id", sa.String(36), nullable=False),
        sa.Column("included_assets", sa.JSON, nullable=True),
        sa.Column("excluded_assets", sa.JSON, nullable=True),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "allocation_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("recommendation_id", sa.String(36), nullable=False, index=True),
        sa.Column("selection_run_id", sa.String(36), nullable=False),
        sa.Column("weights", sa.JSON, nullable=True),
        sa.Column("method", sa.String(100), nullable=True),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "timing_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("recommendation_id", sa.String(36), nullable=False, index=True),
        sa.Column("urgency", sa.String(30), nullable=True),
        sa.Column("horizon_days", sa.Integer, nullable=True),
        sa.Column("entry_signals", sa.JSON, nullable=True),
        sa.Column("exit_signals", sa.JSON, nullable=True),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "risk_overlay_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("recommendation_id", sa.String(36), nullable=False, index=True),
        sa.Column("pre_risk_weights", sa.JSON, nullable=True),
        sa.Column("post_risk_weights", sa.JSON, nullable=True),
        sa.Column("adjustments", sa.JSON, nullable=True),
        sa.Column("constraints_applied", sa.JSON, nullable=True),
        sa.Column("portfolio_risk_score", sa.Float, nullable=True),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # === Domain 4: Signals ===
    op.create_table(
        "signal_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("engine_name", sa.String(100), nullable=False, index=True),
        sa.Column("engine_version", sa.String(50), nullable=True),
        sa.Column("run_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("run_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(30), server_default="completed"),
        sa.Column("data_as_of", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "signal_outputs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("signal_run_id", sa.String(36), nullable=False, index=True),
        sa.Column("asset_id", sa.String(36), nullable=False, index=True),
        sa.Column("score", sa.Float, nullable=True),
        sa.Column("stance", sa.String(30), nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("artifacts", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # === Domain 7: Validation ===
    op.create_table(
        "backtest_experiments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(30), server_default="pending"),
        sa.Column("policy_version_id", sa.String(36), nullable=True),
        sa.Column("universe_id", sa.String(36), nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("config", sa.JSON, nullable=True),
        sa.Column("results_summary", sa.JSON, nullable=True),
        sa.Column("is_promoted", sa.Boolean, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "paper_portfolios",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("current_holdings", sa.JSON, nullable=True),
        sa.Column("cash_weight", sa.Float, server_default=sa.text("1.0")),
        sa.Column("last_rebalance_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_rebalances", sa.Integer, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "replay_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("recommendation_id", sa.String(36), nullable=False, index=True),
        sa.Column("stage", sa.String(50), nullable=False),
        sa.Column("snapshot_data", sa.JSON, nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # === Domain 8: Admin/Ops ===
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("actor", sa.String(100), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("object_type", sa.String(100), nullable=True),
        sa.Column("object_id", sa.String(36), nullable=True),
        sa.Column("details", sa.JSON, nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "incidents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("severity", sa.Integer, nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(30), server_default="open"),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "system_health_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_freshness", sa.JSON, nullable=True),
        sa.Column("feature_health", sa.JSON, nullable=True),
        sa.Column("model_health", sa.JSON, nullable=True),
        sa.Column("publication_health", sa.JSON, nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("system_health_snapshots")
    op.drop_table("incidents")
    op.drop_table("audit_events")
    op.drop_table("replay_snapshots")
    op.drop_table("paper_portfolios")
    op.drop_table("backtest_experiments")
    op.drop_table("signal_outputs")
    op.drop_table("signal_runs")
    op.drop_table("risk_overlay_results")
    op.drop_table("timing_results")
    op.drop_table("allocation_results")
    op.drop_table("selection_runs")
    op.drop_table("recommendation_weights")
    op.drop_table("recommendations")
    op.drop_table("benchmarks")
    op.drop_table("universe_memberships")
    op.drop_table("universes")
    op.drop_table("assets")
