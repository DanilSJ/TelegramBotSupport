from sqlalchemy import Text, ForeignKey, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Message(Base):
    message: Mapped[str] = mapped_column(Text)
    id_message: Mapped[int] = mapped_column(BigInteger)
    ai_message: Mapped[str] = mapped_column(Text, nullable=True)

    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.topic_id"), nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)

    topic: Mapped["Topic"] = relationship("Topic", back_populates="messages")
    user: Mapped["User"] = relationship("User", back_populates="messages")
