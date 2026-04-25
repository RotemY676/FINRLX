"""Add policy_rules and policy_rule_history tables.

Revision ID: 013_policy_rules
Revises: 012_ml_promo
Create Date: 2026-04-25

Phase 6F: editable policy constraints for publication gates and risk overlay.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "013_policy_rules"
down_revision: Union[str, None] = "012_ml_promo"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "policy_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("key", sa.String(80), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("severity", sa.String(20), nullable=False, server_default="warning"),
        sa.Column("threshold_value", sa.Float, nullable=True),
        sa.Column("threshold_unit", sa.String(30), nullable=True),
        sa.Column("applies_to", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("1")),
        sa.Column("is_enforced", sa.Boolean, server_default=sa.text("0")),
        sa.Column("version", sa.Integer, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "policy_rule_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("policy_rule_id", sa.String(36), nullable=False, index=True),
        sa.Column("policy_rule_key", sa.String(80), nullable=False),
        sa.Column("previous_value", sa.Float, nullable=True),
        sa.Column("new_value", sa.Float, nullable=True),
        sa.Column("actor", sa.String(100), nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("policy_rule_history")
    op.drop_table("policy_rules")
