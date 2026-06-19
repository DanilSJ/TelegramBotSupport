from sqlalchemy import Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Message(Base):
    message: Mapped[str] = mapped_column(Text)
    ai_message: Mapped[str] = mapped_column(Text, nullable=True)

    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.topic_id"), nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    topic: Mapped["Topic"] = relationship("Topic", back_populates="messages")
    user: Mapped["User"] = relationship("User", back_populates="messages")
