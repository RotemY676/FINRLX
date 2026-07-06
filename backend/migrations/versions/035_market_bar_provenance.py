"""LEAP F1: per-bar provenance + quality flag on market_bars (D7/D8).

Additive-only (D24): three nullable columns; downgrade drops them.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "035_market_bar_provenance"
down_revision: Union[str, None] = "034_universe_membership_removed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("market_bars", sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("market_bars", sa.Column("chain_position", sa.Integer(), nullable=True))
    op.add_column("market_bars", sa.Column("quality_flag", sa.String(length=30), nullable=True))


def downgrade() -> None:
    op.drop_column("market_bars", "quality_flag")
    op.drop_column("market_bars", "chain_position")
    op.drop_column("market_bars", "fetched_at")
