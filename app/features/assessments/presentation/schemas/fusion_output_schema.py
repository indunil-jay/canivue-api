from pydantic import BaseModel

from app.features.assessments.presentation.schemas.modality_result_schema import (
    ModalityResultSchema,
)


class FusionOutputSchema(BaseModel):
    condition: str
    category: str
    final_confidence_percent: float
    severity_label: str
    modalities: list[ModalityResultSchema]
    notes: list[str]
