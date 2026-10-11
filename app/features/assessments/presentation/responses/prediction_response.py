from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.features.assessments.domain.constants import SAFETY_NOTICE
from app.features.assessments.domain.enums.prediction_status import PredictionStatus
from app.features.assessments.presentation.schemas.model_contribution_schema import (
    ModelContributionSchema,
)


class PredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

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
    model_contributions: list[ModelContributionSchema]
    data_quality_note: str
    historical_comparison_note: str
    outcome_note: str | None
    safety_notice: str = SAFETY_NOTICE
