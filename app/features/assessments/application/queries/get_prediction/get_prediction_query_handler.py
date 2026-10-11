from app.features.assessments.application.interfaces.repositories.prediction_repository import (
    PredictionRepositoryProtocol,
)
from app.features.assessments.application.queries.get_prediction.get_prediction_query import (
    GetPredictionQuery,
)
from app.features.assessments.domain.entities.prediction import Prediction
from app.features.assessments.domain.exceptions import PredictionNotFoundError
from app.features.dogs.application.services.dog_access import DogAccess


class GetPredictionQueryHandler:
    def __init__(self, predictions: PredictionRepositoryProtocol, access: DogAccess):
        self._predictions = predictions
        self._access = access

    async def handle(self, query: GetPredictionQuery) -> Prediction:
        dog = await self._access.readable(query.actor, query.dog_id)
        prediction = await self._predictions.get_by_id(query.prediction_id)
        if prediction is None or prediction.dog_id != dog.id:
            raise PredictionNotFoundError()
        return prediction
