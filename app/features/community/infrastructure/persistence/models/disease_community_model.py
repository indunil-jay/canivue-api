from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import UuidTimestampMixin


class DiseaseCommunityModel(UuidTimestampMixin, Base):
    __tablename__ = "disease_communities"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
