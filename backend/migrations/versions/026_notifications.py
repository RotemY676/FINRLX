"""Phase OP-3 — notifications log."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "026_notifications"
down_revision: Union[str, None] = "025_job_runs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("incident_id", sa.String(36), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="sent"),
        sa.Column("subject", sa.String(300), nullable=False),
        sa.Column("body_preview", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "incident_id", "channel", name="uq_notifications_incident_channel",
        ),
    )
    op.create_index(
        "ix_notifications_incident", "notifications", ["incident_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_incident", "notifications")
    op.drop_table("notifications")
