"""Phase 7: stance_observations — prospective, forward-scored track record.

Additive; downgrade drops it. Capture starts before the reporting surface is
useful on purpose: a forward record can only accumulate in wall-clock time, so
every day without the table is a day of evidence that cannot be recovered.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "037_stance_observations"
down_revision: Union[str, None] = "036_autopilot_dossiers"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stance_observations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("stance", sa.String(length=24), nullable=False),
        sa.Column("composite_score", sa.Float(), nullable=False),
        sa.Column("avg_confidence", sa.Float(), nullable=True),
        sa.Column("uncertainty_tier", sa.String(length=16), nullable=True),
        sa.Column("config_version", sa.String(length=64), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("observed_bar_date", sa.Date(), nullable=False),
        sa.Column("observed_close", sa.Float(), nullable=False),
        sa.Column("horizon_days", sa.Integer(), nullable=False),
        # NULL until the horizon has actually elapsed. Never 0 — that would
        # read as a measured flat outcome rather than "not yet knowable".
        sa.Column("scored_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome_bar_date", sa.Date(), nullable=True),
        sa.Column("outcome_close", sa.Float(), nullable=True),
        sa.Column("realized_return", sa.Float(), nullable=True),
    )
    op.create_index("ix_stance_obs_ticker", "stance_observations", ["ticker"])
    op.create_index("ix_stance_obs_observed_at", "stance_observations", ["observed_at"])


def downgrade() -> None:
    op.drop_index("ix_stance_obs_observed_at", table_name="stance_observations")
    op.drop_index("ix_stance_obs_ticker", table_name="stance_observations")
    op.drop_table("stance_observations")
