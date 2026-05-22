"""Phase 18.6.1 — ticker_insights.metrics JSON column.

Adds the structured-metrics block the LLM now emits as part of its
response. The frontend renders it as a multi-series chart matching
PriceChartCard's style. Nullable for backwards-compat: rows generated
before this migration carry NULL and the FE falls back to
"narrative-only" mode.

Revision string: 27 chars (under the 32-char alembic cap).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "033_ticker_insights_metrics"
down_revision: Union[str, None] = "032_ticker_insights"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("ticker_insights") as batch:
        batch.add_column(sa.Column("metrics", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("ticker_insights") as batch:
        batch.drop_column("metrics")
