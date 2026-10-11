from app.features.assessments.application.dtos.prediction_output_dto import PredictionOutputDTO
from app.features.assessments.application.interfaces.repositories.prediction_repository import (
    PredictionRepositoryProtocol,
)
from app.features.assessments.application.mappers.prediction_dto_mapper import PredictionDTOMapper
from app.features.assessments.application.queries.list_predictions.list_predictions_query import (
    ListPredictionsQuery,
)
from app.features.dogs.application.services.dog_access import DogAccess


class ListPredictionsQueryHandler:
    def __init__(self, predictions: PredictionRepositoryProtocol, access: DogAccess):
        self._predictions = predictions
        self._access = access

    async def handle(self, query: ListPredictionsQuery) -> list[PredictionOutputDTO]:
        dog = await self._access.readable(query.actor, query.dog_id)
        return [
            PredictionDTOMapper.to_output_dto(item)
            for item in await self._predictions.list_for_dog(dog.id)
        ]
