from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Champion(Base):
    __tablename__ = "champions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    cost: Mapped[int] = mapped_column(Integer, nullable=False)
    traits: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    best_items: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    item_reasoning: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    splash_url: Mapped[str | None] = mapped_column(String, nullable=True)
