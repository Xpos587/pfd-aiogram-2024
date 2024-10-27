from sqlalchemy import BigInteger, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from .base import Base


class DBFeedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    user: Mapped[int] = mapped_column(BigInteger)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    is_helpful: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    checklist: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
