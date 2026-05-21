"""Phase W-1 — investor profile tables.

Adds three tables:
* ``investor_profiles`` — current snapshot per user (1:1).
* ``investor_profile_revisions`` — append-only history.
* ``profile_questions`` — seeded catalog the wizard renders from.

Down-migration drops all three; no FK joins to other tables (user_id is
held as a loose string, matching the pattern used by ``saved_views``).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "021_investor_profiles"
down_revision: Union[str, None] = "020_saved_views"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "investor_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("risk_bucket", sa.String(40), nullable=False),
        sa.Column("horizon_band", sa.String(20), nullable=False),
        sa.Column("primary_goal", sa.String(40), nullable=False),
        sa.Column("max_drawdown_pct", sa.Float(), nullable=False),
        sa.Column("knowledge_level", sa.String(20), nullable=False),
        sa.Column("years_investing", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "instruments_traded_json",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
        sa.Column("investable_amount_band", sa.String(20), nullable=False),
        sa.Column("income_band", sa.String(20), nullable=False),
        sa.Column("liquid_net_worth_band", sa.String(20), nullable=False),
        sa.Column(
            "sector_whitelist_json",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
        sa.Column(
            "sector_blacklist_json",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
        sa.Column("region_preference", sa.String(10), nullable=False, server_default="global"),
        sa.Column(
            "exclude_leverage", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("base_currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column(
            "trading_frequency", sa.String(20), nullable=False, server_default="monthly"
        ),
        sa.Column(
            "raw_answers_json",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_investor_profiles_user",
        "investor_profiles",
        ["user_id"],
        unique=True,
    )

    op.create_table(
        "investor_profile_revisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("profile_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column("change_summary", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_investor_profile_revisions_profile",
        "investor_profile_revisions",
        ["profile_id"],
    )
    op.create_index(
        "ix_investor_profile_revisions_user",
        "investor_profile_revisions",
        ["user_id"],
    )

    op.create_table(
        "profile_questions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("step", sa.Integer(), nullable=False),
        sa.Column("order_in_step", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("dimension", sa.String(20), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("helper_text", sa.Text(), nullable=True),
        sa.Column("choices_json", sa.Text(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index(
        "ix_profile_questions_code", "profile_questions", ["code"], unique=True
    )
    op.create_index(
        "ix_profile_questions_step", "profile_questions", ["step", "order_in_step"]
    )


def downgrade() -> None:
    op.drop_index("ix_profile_questions_step", "profile_questions")
    op.drop_index("ix_profile_questions_code", "profile_questions")
    op.drop_table("profile_questions")

    op.drop_index("ix_investor_profile_revisions_user", "investor_profile_revisions")
    op.drop_index("ix_investor_profile_revisions_profile", "investor_profile_revisions")
    op.drop_table("investor_profile_revisions")

    op.drop_index("ix_investor_profiles_user", "investor_profiles")
    op.drop_table("investor_profiles")
