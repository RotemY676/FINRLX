"""Phase OP-2 — job_runs table."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "025_job_runs"
down_revision: Union[str, None] = "024_paper_base_ccy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_key", sa.String(60), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column(
            "triggered_by",
            sa.String(40),
            nullable=False,
            server_default="schedule",
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
    )
    op.create_index("ix_job_runs_job_key", "job_runs", ["job_key"])
    op.create_index("ix_job_runs_status", "job_runs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_job_runs_status", "job_runs")
    op.drop_index("ix_job_runs_job_key", "job_runs")
    op.drop_table("job_runs")
