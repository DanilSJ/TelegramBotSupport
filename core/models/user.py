from sqlalchemy import String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class User(Base):
    username: Mapped[str] = mapped_column(String)
    telegram_id: Mapped[int] = mapped_column(BigInteger)
