from datetime import date

from sqlalchemy import JSON, Boolean, Date, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import UuidTimestampMixin


class DogModel(UuidTimestampMixin, Base):
    __tablename__ = "dogs"

    owner_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    breed: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    color: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    microchip_id: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    avatar_emoji: Mapped[str] = mapped_column(String(16), nullable=False, default="🐶")
    is_neutered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    blood_group: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    primary_vet: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    special_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    allergies: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    existing_conditions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    vaccinations: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    medications: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    insurance: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    photo_file_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
