from dataclasses import dataclass

from app.features.assessments.domain.entities.prediction import Prediction
from app.features.assessments.domain.value_objects.assessment_result import AssessmentResult


@dataclass(frozen=True)
class HealthCheckOutcome:
    prediction: Prediction
    result: AssessmentResult
    dog_name: str
