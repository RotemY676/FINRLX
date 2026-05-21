"""Phase BETA-2 — beta-tester feedback.

Tester writes a short message via /feedback; we capture the surface
they were on + their email (already known via auth) so an admin can
triage without asking for follow-up.

Categories are free-form text (frontend offers a small picklist) so
admin can introduce new categories without a migration.
"""
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import gen_uuid

FEEDBACK_STATUSES = ("open", "triaged", "in_progress", "resolved", "wontfix")


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    user_email: Mapped[str] = mapped_column(String(320), nullable=False)
    surface: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(40), nullable=False, default="general")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
