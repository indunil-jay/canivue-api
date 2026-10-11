from collections.abc import Sequence
from dataclasses import asdict
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.dataclass_repository import DataclassRepository
from app.core.models import UtcDateTime, UuidTimestampMixin
from app.features.assessments.domain.entities import (
    ModelContribution,
    Prediction,
    PredictionRepositoryProtocol,
    PredictionStatus,
)


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


class SqlAlchemyPredictionRepository(
    DataclassRepository[Prediction, PredictionModel], PredictionRepositoryProtocol
):
    _model_cls = PredictionModel
    _entity_cls = Prediction

    def _to_entity(self, model: PredictionModel) -> Prediction:
        prediction = super()._to_entity(model)
        prediction.model_contributions = [ModelContribution(**c) for c in model.model_contributions]
        return prediction

    def _to_model_dict(self, entity: Prediction) -> dict[str, Any]:
        data = super()._to_model_dict(entity)
        data["model_contributions"] = [asdict(c) for c in entity.model_contributions]
        return data

    async def list_for_dog(self, dog_id: str) -> Sequence[Prediction]:
        return await self.find(
            PredictionModel.dog_id == dog_id, order_by=PredictionModel.prediction_date.desc()
        )

    async def latest_active(self, dog_id: str) -> Prediction | None:
        return await self.find_one(
            PredictionModel.dog_id == dog_id,
            PredictionModel.status != PredictionStatus.RESOLVED.value,
            order_by=PredictionModel.prediction_date.desc(),
        )

    async def count_since(self, dog_ids: Sequence[str], since: datetime) -> int:
        if not dog_ids:
            return 0
        return await self.count(
            PredictionModel.dog_id.in_(dog_ids), PredictionModel.prediction_date >= since
        )
