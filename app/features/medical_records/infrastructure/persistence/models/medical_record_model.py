from datetime import datetime

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import UtcDateTime, UuidTimestampMixin


class MedicalRecordModel(UuidTimestampMixin, Base):
    __tablename__ = "medical_records"

    dog_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    date: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False, index=True)
    file_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    author_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    author_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    authored_by_vet: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
