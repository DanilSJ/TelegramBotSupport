from sqlalchemy import String, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class User(Base):
    username: Mapped[str] = mapped_column(String, nullable=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    connect_operator: Mapped[bool] = mapped_column(Boolean, default=False)

    user_topic_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    operator_topic_id: Mapped[int] = mapped_column(BigInteger, nullable=True)

    is_operator: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    is_block: Mapped[bool] = mapped_column(Boolean, default=False)
