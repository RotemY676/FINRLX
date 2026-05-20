"""Phase MVP-1: Identity & tenant boundary.

Adds:
- users
- refresh_tokens
- email_allowlist
- user_id (nullable FK) on recommendations and paper_portfolios for future tenant binding

In MVP-1, user_id columns are nullable. Existing data has user_id NULL. Tenant
enforcement on existing routes is flipped in Phase MVP-4 alongside the frontend
auth UI; MVP-1 ships the schema + the auth endpoints only.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "018_auth_identity"
down_revision: Union[str, None] = "017_reg_meta"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by_id", sa.String(36), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])
    # Hot path for rotation: latest token per user.
    op.create_index(
        "ix_refresh_tokens_user_id_issued_at",
        "refresh_tokens",
        ["user_id", "issued_at"],
    )

    op.create_table(
        "email_allowlist",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("added_by", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email", name="uq_email_allowlist_email"),
    )
    op.create_index("ix_email_allowlist_email", "email_allowlist", ["email"])

    # Tenant-binding columns (nullable in MVP-1; enforced in MVP-4)
    with op.batch_alter_table("recommendations") as batch:
        batch.add_column(sa.Column("user_id", sa.String(36), nullable=True))
    op.create_index("ix_recommendations_user_id", "recommendations", ["user_id"])

    with op.batch_alter_table("paper_portfolios") as batch:
        batch.add_column(sa.Column("user_id", sa.String(36), nullable=True))
    op.create_index("ix_paper_portfolios_user_id", "paper_portfolios", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_paper_portfolios_user_id", "paper_portfolios")
    with op.batch_alter_table("paper_portfolios") as batch:
        batch.drop_column("user_id")

    op.drop_index("ix_recommendations_user_id", "recommendations")
    with op.batch_alter_table("recommendations") as batch:
        batch.drop_column("user_id")

    op.drop_index("ix_email_allowlist_email", "email_allowlist")
    op.drop_table("email_allowlist")

    op.drop_index("ix_refresh_tokens_user_id_issued_at", "refresh_tokens")
    op.drop_index("ix_refresh_tokens_token_hash", "refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", "refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index("ix_users_email", "users")
    op.drop_table("users")
