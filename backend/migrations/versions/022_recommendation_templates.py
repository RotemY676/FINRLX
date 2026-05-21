"""Phase TPL-1 — recommendation_templates table.

Down-migration drops the table cleanly; no FK joins to other tables
(``created_by_user_id`` is held as a loose string per repo convention).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "022_rec_templates"
down_revision: Union[str, None] = "021_investor_profiles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recommendation_templates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("key", sa.String(60), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("badge", sa.String(40), nullable=False),
        sa.Column("risk_bucket", sa.String(40), nullable=False),
        sa.Column("horizon_band", sa.String(20), nullable=False),
        sa.Column("primary_goal", sa.String(40), nullable=False),
        sa.Column("max_drawdown_pct", sa.Float(), nullable=False),
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
        sa.Column(
            "exclude_leverage", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("base_currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column(
            "trading_frequency", sa.String(20), nullable=False, server_default="monthly"
        ),
        sa.Column(
            "region_preference", sa.String(10), nullable=False, server_default="global"
        ),
        sa.Column(
            "is_seed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("created_by_user_id", sa.String(36), nullable=True),
        sa.Column("allocation_summary", sa.String(40), nullable=True),
        sa.Column(
            "last_evaluated_at", sa.DateTime(timezone=True), nullable=True
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
        "ix_recommendation_templates_key",
        "recommendation_templates",
        ["key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_recommendation_templates_key", "recommendation_templates"
    )
    op.drop_table("recommendation_templates")
