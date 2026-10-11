from app.features.assessments.application.commands.record_prediction_outcome.record_prediction_outcome_command import (
    RecordPredictionOutcomeCommand,
)
from app.features.assessments.application.interfaces.repositories.prediction_repository import (
    PredictionRepositoryProtocol,
)
from app.features.assessments.domain.entities.prediction import Prediction
from app.features.assessments.domain.enums.prediction_status import PredictionStatus
from app.features.assessments.domain.exceptions import PredictionNotFoundError
from app.features.dogs.application.services.dog_access import DogAccess
from app.shared.entity import _utc_now


class RecordPredictionOutcomeCommandHandler:
    def __init__(self, predictions: PredictionRepositoryProtocol, access: DogAccess):
        self._predictions = predictions
        self._access = access

    async def handle(self, command: RecordPredictionOutcomeCommand) -> Prediction:
        dog = await self._access.treatable(command.actor, command.dog_id)
        prediction = await self._predictions.get_by_id(command.prediction_id)
        if prediction is None or prediction.dog_id != dog.id:
            raise PredictionNotFoundError()
        prediction.outcome_note = command.outcome_note.strip()
        if command.resolved:
            prediction.status = PredictionStatus.RESOLVED
        prediction.updated_at = _utc_now()
        return await self._predictions.update(prediction)
