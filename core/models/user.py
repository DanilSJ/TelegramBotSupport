from sqlalchemy import String, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
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

    messages: Mapped[list["Message"]] = relationship("Message", back_populates="user")

    ai_message: Mapped[list["Ai_message"]] = relationship(
        "Ai_message", back_populates="user"
    )

    topic: Mapped["Topic"] = relationship(
        "Topic",
        back_populates="user",
        uselist=False,
    )
