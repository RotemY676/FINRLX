"""Phase MVP-3: Recommendation provenance.

Adds tamper-evident provenance fields to recommendations:
- input_hash       SHA-256 of canonical-JSON of the SignalOutput rows used
- policy_hash      SHA-256 of canonical-JSON of pipeline policy constants
- pipeline_version Semantic version of the pipeline that produced the rec
- replay_seed      Per-run seed for any sampling/randomness (UUID)

All columns are nullable for backward compatibility with existing rows.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "019_rec_provenance"
down_revision: Union[str, None] = "018_auth_identity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("recommendations") as batch:
        batch.add_column(sa.Column("input_hash", sa.String(64), nullable=True))
        batch.add_column(sa.Column("policy_hash", sa.String(64), nullable=True))
        batch.add_column(sa.Column("pipeline_version", sa.String(50), nullable=True))
        batch.add_column(sa.Column("replay_seed", sa.String(36), nullable=True))
    op.create_index("ix_recommendations_input_hash", "recommendations", ["input_hash"])


def downgrade() -> None:
    op.drop_index("ix_recommendations_input_hash", "recommendations")
    with op.batch_alter_table("recommendations") as batch:
        batch.drop_column("replay_seed")
        batch.drop_column("pipeline_version")
        batch.drop_column("policy_hash")
        batch.drop_column("input_hash")
