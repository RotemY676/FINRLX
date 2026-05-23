"""Phase 20.2 — universe_memberships.removed_at (soft-delete column).

Membership rows previously had only `added_at`; removing an asset meant a
hard DELETE, which broke replay of historical recommendations referencing
that membership. Adding a nullable `removed_at` lets us:

  - keep the row (preserves the (universe_id, asset_id) composite PK and the
    historical association)
  - flag the row as "no longer a current member" by setting `removed_at`
  - re-add the same (universe, asset) pair by clearing `removed_at` instead
    of attempting an INSERT that would violate the composite PK

Existing rows get NULL (= currently a member), which matches their pre-
migration semantics — no data backfill needed.

Revision string: 32-char cap respected.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "034_universe_membership_removed"
down_revision: Union[str, None] = "033_ticker_insights_metrics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("universe_memberships") as batch:
        batch.add_column(
            sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("universe_memberships") as batch:
        batch.drop_column("removed_at")
