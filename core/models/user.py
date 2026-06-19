from sqlalchemy import String, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class User(Base):
    username: Mapped[str] = mapped_column(String)
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    connect_operator: Mapped[bool] = mapped_column(Boolean)

    user_topic_id: Mapped[int] = mapped_column(BigInteger)
    operator_topic_id: Mapped[int] = mapped_column(BigInteger)

    is_operator: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
