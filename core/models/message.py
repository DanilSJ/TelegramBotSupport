from sqlalchemy import Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Message(Base):
    message: Mapped[str] = mapped_column(Text)

    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.topic_id"))

    topic: Mapped["Topic"] = relationship("Topic", back_populates="messages")
