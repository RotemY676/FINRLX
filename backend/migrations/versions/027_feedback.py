"""Phase BETA-2 — feedback table."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "027_feedback"
down_revision: Union[str, None] = "026_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feedback",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("user_email", sa.String(320), nullable=False),
        sa.Column("surface", sa.String(100), nullable=True),
        sa.Column("category", sa.String(40), nullable=False, server_default="general"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_feedback_user", "feedback", ["user_id"])
    op.create_index("ix_feedback_status", "feedback", ["status"])


def downgrade() -> None:
    op.drop_index("ix_feedback_status", "feedback")
    op.drop_index("ix_feedback_user", "feedback")
    op.drop_table("feedback")
