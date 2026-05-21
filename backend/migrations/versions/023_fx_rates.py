"""Phase FX-1 — fx_rates table."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "023_fx_rates"
down_revision: Union[str, None] = "022_rec_templates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fx_rates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("base_currency", sa.String(3), nullable=False),
        sa.Column("quote_currency", sa.String(3), nullable=False),
        sa.Column("rate_date", sa.Date(), nullable=False),
        sa.Column("rate", sa.Float(), nullable=False),
        sa.Column("source", sa.String(40), nullable=False, server_default="frankfurter"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "base_currency", "quote_currency", "rate_date", "source",
            name="uq_fx_rates_base_quote_date_source",
        ),
    )
    op.create_index("ix_fx_rates_base", "fx_rates", ["base_currency"])
    op.create_index("ix_fx_rates_quote", "fx_rates", ["quote_currency"])
    op.create_index("ix_fx_rates_date", "fx_rates", ["rate_date"])


def downgrade() -> None:
    op.drop_index("ix_fx_rates_date", "fx_rates")
    op.drop_index("ix_fx_rates_quote", "fx_rates")
    op.drop_index("ix_fx_rates_base", "fx_rates")
    op.drop_table("fx_rates")
