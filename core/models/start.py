from sqlalchemy import Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class Start(Base):
    text: Mapped[str] = mapped_column(Text)
    is_use: Mapped[bool] = mapped_column(Boolean, default=False)
