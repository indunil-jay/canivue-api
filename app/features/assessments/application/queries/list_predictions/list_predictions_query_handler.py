from collections.abc import Sequence

from app.features.assessments.application.interfaces.repositories.prediction_repository import (
    PredictionRepositoryProtocol,
)
from app.features.assessments.application.queries.list_predictions.list_predictions_query import (
    ListPredictionsQuery,
)
from app.features.assessments.domain.entities.prediction import Prediction
from app.features.dogs.application.services.dog_access import DogAccess


class ListPredictionsQueryHandler:
    def __init__(self, predictions: PredictionRepositoryProtocol, access: DogAccess):
        self._predictions = predictions
        self._access = access

    async def handle(self, query: ListPredictionsQuery) -> Sequence[Prediction]:
        dog = await self._access.readable(query.actor, query.dog_id)
        return await self._predictions.list_for_dog(dog.id)
