from sqlalchemy import Enum, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Augment(Base):
    __tablename__ = "augments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    tier: Mapped[str] = mapped_column(
        Enum("Silver", "Gold", "Prismatic", name="augment_tier_enum"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    comp_synergy: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
