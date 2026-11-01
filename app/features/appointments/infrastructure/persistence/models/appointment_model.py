from datetime import datetime

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import UtcDateTime, UuidTimestampMixin


class AppointmentModel(UuidTimestampMixin, Base):
    __tablename__ = "appointments"

    owner_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    owner_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    vet_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    vet_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    vet_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    dog_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    dog_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    date_time: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    consultation_type: Mapped[str] = mapped_column(String(20), nullable=False)
    fee_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
