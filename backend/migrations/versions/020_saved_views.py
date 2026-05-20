"""Phase B3: Saved views per user.

Replaces the hardcoded "Saved views" pile in the sidebar with a real
table. Each row is one user's named view — a label, a scope ("decision",
"paper", "ops", etc.), a serialized filter dict (JSON), and an optional
tone (the colored dot the sidebar renders next to the label).

Down-migration drops the table cleanly; no joins to other tables.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "020_saved_views"
down_revision: Union[str, None] = "019_rec_provenance"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "saved_views",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("scope", sa.String(40), nullable=False),
        sa.Column("filters_json", sa.Text(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("tone", sa.String(20), nullable=True),
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
    op.create_index("ix_saved_views_user", "saved_views", ["user_id"])
    op.create_index("ix_saved_views_user_scope", "saved_views", ["user_id", "scope"])


def downgrade() -> None:
    op.drop_index("ix_saved_views_user_scope", "saved_views")
    op.drop_index("ix_saved_views_user", "saved_views")
    op.drop_table("saved_views")
