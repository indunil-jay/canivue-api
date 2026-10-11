from sqlalchemy import JSON, Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import UuidTimestampMixin


class VetProfileModel(UuidTimestampMixin, Base):
    __tablename__ = "vet_profiles"

    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    specialty: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    specialties: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    experience_years: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consultation_fee_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    response_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    languages: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    consultation_types: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    bio: Mapped[str] = mapped_column(Text, nullable=False, default="")
    clinics: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    qualifications: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    availability: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
