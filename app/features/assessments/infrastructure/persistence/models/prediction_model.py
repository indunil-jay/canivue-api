from datetime import datetime

from sqlalchemy import JSON, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import UtcDateTime, UuidTimestampMixin


class PredictionModel(UuidTimestampMixin, Base):
    __tablename__ = "predictions"

    dog_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    combined_risk_percent: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_percent: Mapped[float] = mapped_column(Float, nullable=False)
    prediction_date: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    affected_indicators: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    recommended_next_step: Mapped[str] = mapped_column(Text, nullable=False, default="")
    model_contributions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    data_quality_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    historical_comparison_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    outcome_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_file_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    assessment: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
