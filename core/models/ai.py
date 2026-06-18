from sqlalchemy import String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class AI(Base):
    model: Mapped[str] = mapped_column(String)
    base_url: Mapped[str] = mapped_column(String)
    api_key: Mapped[str] = mapped_column(Text)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=True)
    use: Mapped[bool] = mapped_column(Boolean, default=False)
