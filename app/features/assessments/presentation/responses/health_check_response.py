from datetime import datetime

from pydantic import BaseModel

from app.features.assessments.domain.constants import SAFETY_NOTICE
from app.features.assessments.presentation.schemas.fusion_output_schema import FusionOutputSchema
from app.features.assessments.presentation.schemas.progression_output_schema import (
    ProgressionOutputSchema,
)


class HealthCheckResponse(BaseModel):
    prediction_id: str
    dog_name: str
    fusion: FusionOutputSchema
    progression: ProgressionOutputSchema
    generated_at: datetime
    model_version: str
    safety_notice: str = SAFETY_NOTICE
