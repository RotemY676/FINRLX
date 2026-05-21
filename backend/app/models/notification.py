"""Phase OP-3 — notification audit log.

One row per (incident_id, channel) so the notifier never re-sends.
"""
from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import gen_uuid

NOTIFICATION_STATUSES = ("sent", "skipped", "failed")
NOTIFICATION_CHANNELS = ("webhook", "smtp")


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint(
            "incident_id", "channel", name="uq_notifications_incident_channel",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    incident_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="sent")
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    body_preview: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
