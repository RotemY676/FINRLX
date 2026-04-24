"""Engine definition registry.

Maps to Data Model doc 11, Domain 4: Signal and Engine Output (registry extension).
"""
from sqlalchemy import String, Text, JSON, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, gen_uuid


class EngineDefinition(Base, TimestampMixin):
    __tablename__ = "engine_definitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    key: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # momentum, risk, sentiment, composite
    description: Mapped[str | None] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")
    required_feature_keys: Mapped[list | None] = mapped_column(JSON)
    output_kind: Mapped[str] = mapped_column(String(20), nullable=False, default="signal")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
