from dataclasses import dataclass
from datetime import datetime

from app.features.assessments.domain.enums.prediction_status import PredictionStatus
from app.features.assessments.domain.value_objects.model_contribution import ModelContribution


@dataclass(frozen=True)
class PredictionOutputDTO:
    id: str
    dog_id: str
    title: str
    category: str
    status: PredictionStatus
    combined_risk_percent: float
    confidence_percent: float
    prediction_date: datetime
    model_version: str
    affected_indicators: list[str]
    recommended_next_step: str
    model_contributions: list[ModelContribution]
    data_quality_note: str
    historical_comparison_note: str
    outcome_note: str | None
    image_file_id: str | None
    assessment: dict
    created_at: datetime
    updated_at: datetime | None
