"""Add research_registry_metadata table for Postgres metadata mirror."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "017_reg_meta"
down_revision: Union[str, None] = "016_rl_bench"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "research_registry_metadata",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("registry_kind", sa.String(50), nullable=False),
        sa.Column("record_id", sa.String(100), nullable=False),
        sa.Column("record_hash", sa.String(200), nullable=True),
        sa.Column("record_state", sa.String(50), nullable=True),
        sa.Column("display_name", sa.String(300), nullable=True),
        sa.Column("source_registry_path", sa.String(500), nullable=True),
        sa.Column("artifact_path", sa.String(500), nullable=True),
        sa.Column("metadata_summary_json", sa.JSON, nullable=True),
        sa.Column("warnings_json", sa.JSON, nullable=True),
        sa.Column("limitations_json", sa.JSON, nullable=True),
        sa.Column("mirror_status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("research_only", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("offline_only", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("no_production_influence", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("registry_kind", "record_id", name="uq_registry_kind_record_id"),
    )
    op.create_index("ix_rrm_registry_kind", "research_registry_metadata", ["registry_kind"])
    op.create_index("ix_rrm_record_id", "research_registry_metadata", ["record_id"])
    op.create_index("ix_rrm_mirror_status", "research_registry_metadata", ["mirror_status"])
    op.create_index("ix_rrm_last_seen_at", "research_registry_metadata", ["last_seen_at"])


def downgrade() -> None:
    op.drop_index("ix_rrm_last_seen_at", "research_registry_metadata")
    op.drop_index("ix_rrm_mirror_status", "research_registry_metadata")
    op.drop_index("ix_rrm_record_id", "research_registry_metadata")
    op.drop_index("ix_rrm_registry_kind", "research_registry_metadata")
    op.drop_table("research_registry_metadata")
