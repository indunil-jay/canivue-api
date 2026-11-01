from datetime import datetime

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import UtcDateTime, UuidTimestampMixin


class SubscriptionModel(UuidTimestampMixin, Base):
    __tablename__ = "subscriptions"

    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    plan_id: Mapped[str] = mapped_column(String(30), nullable=False)
    period_start: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    renews_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
