from app.features.assessments.application.dtos.prediction_output_dto import PredictionOutputDTO
from app.features.assessments.application.interfaces.repositories.prediction_repository import (
    PredictionRepositoryProtocol,
)
from app.features.assessments.application.mappers.prediction_dto_mapper import PredictionDTOMapper
from app.features.assessments.application.queries.get_latest_prediction.get_latest_prediction_query import (
    GetLatestPredictionQuery,
)
from app.features.dogs.application.services.dog_access import DogAccess


class GetLatestPredictionQueryHandler:
    def __init__(self, predictions: PredictionRepositoryProtocol, access: DogAccess):
        self._predictions = predictions
        self._access = access

    async def handle(self, query: GetLatestPredictionQuery) -> PredictionOutputDTO | None:
        dog = await self._access.readable(query.actor, query.dog_id)
        return (
            PredictionDTOMapper.to_output_dto(found)
            if (found := await self._predictions.latest_active(dog.id))
            else None
        )
