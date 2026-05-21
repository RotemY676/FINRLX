"""Phase FX-2 — paper_portfolios.base_currency.

Adds a non-null ``base_currency`` column (default ``'USD'``) so existing
rows are backfilled in place. Downgrade drops the column.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "024_paper_base_ccy"
down_revision: Union[str, None] = "023_fx_rates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("paper_portfolios") as batch:
        batch.add_column(
            sa.Column(
                "base_currency",
                sa.String(3),
                nullable=False,
                server_default="USD",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("paper_portfolios") as batch:
        batch.drop_column("base_currency")
