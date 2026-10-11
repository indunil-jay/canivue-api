from datetime import datetime

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import UtcDateTime, UuidTimestampMixin


class ReviewModel(UuidTimestampMixin, Base):
    __tablename__ = "vet_reviews"

    appointment_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    vet_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    owner_id: Mapped[int] = mapped_column(Integer, nullable=False)
    owner_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False, default="")
    date: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
