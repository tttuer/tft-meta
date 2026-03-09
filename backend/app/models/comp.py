import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Comp(Base):
    __tablename__ = "comps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    tier: Mapped[str] = mapped_column(Enum("S", "A", "B", "C", name="tier_enum"), nullable=False)
    win_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    top4_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_placement: Mapped[float] = mapped_column(Float, nullable=False, default=4.0)
    play_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    core_units: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    board_positions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    recommended_augments: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    entry_conditions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    patch_version: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
