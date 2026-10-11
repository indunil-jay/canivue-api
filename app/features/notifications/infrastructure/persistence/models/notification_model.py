from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import UuidTimestampMixin


class NotificationModel(UuidTimestampMixin, Base):
    __tablename__ = "notifications"

    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    dog_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    action_label: Mapped[str | None] = mapped_column(String(60), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
