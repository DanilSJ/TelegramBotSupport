from sqlalchemy import Text, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class Ai_message(Base):
    message: Mapped[str] = mapped_column(Text)
    id_message: Mapped[int] = mapped_column(BigInteger)
    ai_message: Mapped[str] = mapped_column(Text, nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
