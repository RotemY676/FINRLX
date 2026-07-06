"""LEAP S2: autopilot_dossiers table (D34). Additive; downgrade drops it."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "036_autopilot_dossiers"
down_revision: Union[str, None] = "035_market_bar_provenance"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "autopilot_dossiers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("latest_bar_date", sa.String(length=10), nullable=False),
        sa.Column("config_version", sa.String(length=40), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_autopilot_dossier_ticker", "autopilot_dossiers", ["ticker"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_autopilot_dossier_ticker", table_name="autopilot_dossiers")
    op.drop_table("autopilot_dossiers")
