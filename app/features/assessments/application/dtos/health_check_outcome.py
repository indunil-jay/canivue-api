from dataclasses import dataclass

from app.features.assessments.application.dtos.prediction_output_dto import PredictionOutputDTO
from app.features.assessments.domain.value_objects.assessment_result import AssessmentResult


@dataclass(frozen=True)
class HealthCheckOutcome:
    prediction: PredictionOutputDTO
    result: AssessmentResult
    dog_name: str
