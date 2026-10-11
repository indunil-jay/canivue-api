from collections.abc import Sequence
from dataclasses import asdict
from datetime import datetime
from typing import Any

from app.core.dataclass_repository import DataclassRepository
from app.features.assessments.application.interfaces.repositories.prediction_repository import (
    PredictionRepositoryProtocol,
)
from app.features.assessments.domain.entities.prediction import Prediction
from app.features.assessments.domain.enums.prediction_status import PredictionStatus
from app.features.assessments.domain.value_objects.model_contribution import ModelContribution
from app.features.assessments.infrastructure.persistence.models.prediction_model import (
    PredictionModel,
)


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
