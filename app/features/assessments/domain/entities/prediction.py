from dataclasses import dataclass, field
from datetime import datetime

from app.features.assessments.domain.enums.prediction_status import PredictionStatus
from app.features.assessments.domain.value_objects.model_contribution import ModelContribution
from app.shared.entity import BaseEntity, _utc_now


@dataclass
class Prediction(BaseEntity):
    dog_id: str = ""
    title: str = ""
    category: str = ""
    status: PredictionStatus = PredictionStatus.MONITORING
    combined_risk_percent: float = 0.0
    confidence_percent: float = 0.0
    prediction_date: datetime = field(default_factory=_utc_now)
    model_version: str = ""
    affected_indicators: list[str] = field(default_factory=list)
    recommended_next_step: str = ""
    model_contributions: list[ModelContribution] = field(default_factory=list)
    data_quality_note: str = ""
    historical_comparison_note: str = ""
    outcome_note: str | None = None
    image_file_id: str | None = None
    # The full Assessment (fusion and progression) as plain data, for the detail view.
    assessment: dict = field(default_factory=dict)
