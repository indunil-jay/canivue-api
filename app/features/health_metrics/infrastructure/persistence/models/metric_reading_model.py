from datetime import datetime

from sqlalchemy import Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import UtcDateTime, UuidTimestampMixin


class MetricReadingModel(UuidTimestampMixin, Base):
    __tablename__ = "metric_readings"
    __table_args__ = (Index("ix_metric_readings_lookup", "dog_id", "metric", "recorded_at"),)

    dog_id: Mapped[str] = mapped_column(String(36), nullable=False)
    metric: Mapped[str] = mapped_column(String(20), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
