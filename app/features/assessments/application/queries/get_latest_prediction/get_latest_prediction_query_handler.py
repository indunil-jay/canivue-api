from app.features.assessments.application.interfaces.repositories.prediction_repository import (
    PredictionRepositoryProtocol,
)
from app.features.assessments.application.queries.get_latest_prediction.get_latest_prediction_query import (
    GetLatestPredictionQuery,
)
from app.features.assessments.domain.entities.prediction import Prediction
from app.features.dogs.application.services.dog_access import DogAccess


class GetLatestPredictionQueryHandler:
    def __init__(self, predictions: PredictionRepositoryProtocol, access: DogAccess):
        self._predictions = predictions
        self._access = access

    async def handle(self, query: GetLatestPredictionQuery) -> Prediction | None:
        dog = await self._access.readable(query.actor, query.dog_id)
        return await self._predictions.latest_active(dog.id)
