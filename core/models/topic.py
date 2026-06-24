from sqlalchemy import String, BigInteger, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Topic(Base):
    name: Mapped[str] = mapped_column(String)
    topic_id: Mapped[int] = mapped_column(BigInteger, unique=True)

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), unique=True, nullable=True
    )

    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)

    user: Mapped["User"] = relationship(
        "User",
        back_populates="topic",
        uselist=False,
    )

    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="topic",
        cascade="all, delete-orphan",
    )
