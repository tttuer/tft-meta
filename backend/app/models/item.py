from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    components: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    is_component: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
