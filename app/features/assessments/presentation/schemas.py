from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.features.assessments.application.use_cases import HealthCheckOutcome
from app.features.assessments.domain.entities import (
    SAFETY_NOTICE,
    Prediction,
    PredictionStatus,
    RiskLevel,
)


class ModalityResultSchema(BaseModel):
    name: str
    available: bool
    confidence_percent: float
    quality_percent: float
    contribution_percent: float


class FusionOutputSchema(BaseModel):
    condition: str
    category: str
    final_confidence_percent: float
    severity_label: str
    modalities: list[ModalityResultSchema]
    notes: list[str]


class RiskFactorSchema(BaseModel):
    label: str
    score_percent: float
    weight_percent: float
    contribution_points: float


class ProgressionOutputSchema(BaseModel):
    horizon_days: int
    risk_percent: float
    risk_level: RiskLevel
    factors: list[RiskFactorSchema]
    main_reasons: list[str]
    recommendation: str
    missing_data_note: str | None


class HealthCheckResponse(BaseModel):
    prediction_id: str
    dog_name: str
    fusion: FusionOutputSchema
    progression: ProgressionOutputSchema
    generated_at: datetime
    model_version: str
    safety_notice: str = SAFETY_NOTICE

    @classmethod
    def of(cls, prediction: Prediction) -> "HealthCheckResponse":
        return cls(
            prediction_id=prediction.id,
            generated_at=prediction.prediction_date,
            model_version=prediction.model_version,
            **prediction.assessment,
        )

    @classmethod
    def of_outcome(cls, outcome: HealthCheckOutcome) -> "HealthCheckResponse":
        return cls.of(outcome.prediction)


class ModelContributionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    model_name: str
    contribution_percent: float


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


class PredictionOutcomeRequest(BaseModel):
    outcome_note: str = Field(..., min_length=1, max_length=2000)
    resolved: bool = False
