from sqlalchemy import String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class Topic(Base):
    name: Mapped[str] = mapped_column(String)
    topic_Id: Mapped[int] = mapped_column(BigInteger)

