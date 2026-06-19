from sqlalchemy import String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Topic(Base):
    name: Mapped[str] = mapped_column(String)
    topic_id: Mapped[int] = mapped_column(BigInteger)

    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="topic",
        cascade="all, delete-orphan",
    )
