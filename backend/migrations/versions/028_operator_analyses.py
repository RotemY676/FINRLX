"""Phase O-0 — operator analysis archive.

Stores LLM responses pasted back by the operator (currently a single user)
after running them through ChatGPT or Claude with context exported from the
Decision / Replay / News surfaces. Joined back to a recommendation_id so the
Replay view can surface them as "Analyst notes."
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "028_operator_analyses"
down_revision: Union[str, None] = "027_feedback"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "operator_analyses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("user_email", sa.String(320), nullable=False),
        # The surface the context was exported from (decision, replay, news, manual).
        sa.Column("surface", sa.String(40), nullable=False),
        # Optional foreign-key-style link to a recommendation; nullable because
        # /news exports are not tied to a single recommendation.
        sa.Column("recommendation_id", sa.String(36), nullable=True),
        # Which LLM the operator used (gpt, claude, other) — free-form short string.
        sa.Column("source", sa.String(20), nullable=False, server_default="other"),
        # The exact prompt that was copied; useful for reproducing the analysis.
        sa.Column("prompt", sa.Text(), nullable=True),
        # The pasted-back response.
        sa.Column("response", sa.Text(), nullable=False),
        # Free-form note from the operator.
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_operator_analyses_user", "operator_analyses", ["user_id"])
    op.create_index(
        "ix_operator_analyses_recommendation",
        "operator_analyses",
        ["recommendation_id"],
    )
    op.create_index("ix_operator_analyses_surface", "operator_analyses", ["surface"])


def downgrade() -> None:
    op.drop_index("ix_operator_analyses_surface", "operator_analyses")
    op.drop_index("ix_operator_analyses_recommendation", "operator_analyses")
    op.drop_index("ix_operator_analyses_user", "operator_analyses")
    op.drop_table("operator_analyses")
