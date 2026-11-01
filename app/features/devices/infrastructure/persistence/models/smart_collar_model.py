from datetime import datetime

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import UtcDateTime, UuidTimestampMixin


class SmartCollarModel(UuidTimestampMixin, Base):
    __tablename__ = "smart_collars"

    dog_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    battery_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    firmware_version: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    sync_history: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    granted_permissions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
