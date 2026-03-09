from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MatchRaw(Base):
    __tablename__ = "match_raw"

    match_id: Mapped[str] = mapped_column(String, primary_key=True)
    region: Mapped[str] = mapped_column(String, nullable=False)
    participants: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    patch_version: Mapped[str] = mapped_column(String, nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
