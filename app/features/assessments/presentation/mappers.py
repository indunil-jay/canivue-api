from app.features.assessments.application.dtos.health_check_outcome import HealthCheckOutcome
from app.features.assessments.application.dtos.prediction_output_dto import PredictionOutputDTO
from app.features.assessments.presentation.responses.health_check_response import (
    HealthCheckResponse,
)


class AssessmentsPresentationMapper:
    @staticmethod
    def to_health_check_response(prediction: PredictionOutputDTO) -> HealthCheckResponse:
        return HealthCheckResponse(
            prediction_id=prediction.id,
            generated_at=prediction.prediction_date,
            model_version=prediction.model_version,
            **prediction.assessment,
        )

    @staticmethod
    def to_health_check_response_from_outcome(outcome: HealthCheckOutcome) -> HealthCheckResponse:
        return AssessmentsPresentationMapper.to_health_check_response(outcome.prediction)
