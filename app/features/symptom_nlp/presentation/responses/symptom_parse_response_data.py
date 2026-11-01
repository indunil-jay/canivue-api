from pydantic import BaseModel, Field

from app.features.symptom_nlp.presentation.schemas.body_location_schema import BodyLocationSchema
from app.features.symptom_nlp.presentation.schemas.duration_schema import DurationSchema
from app.features.symptom_nlp.presentation.schemas.emergency_triage_schema import (
    EmergencyTriageSchema,
)
from app.features.symptom_nlp.presentation.schemas.extracted_span_schema import ExtractedSpanSchema


class SymptomParseResponseData(BaseModel):
    raw_text: str
    symptoms: list[str] = Field(default_factory=list)
    negated_symptoms: list[str] = Field(default_factory=list)
    body_locations: list[BodyLocationSchema] = Field(default_factory=list)
    duration: DurationSchema | None = None
    frequency: dict[str, str] | None = None
    severity_cues: list[str] = Field(default_factory=list)
    new_symptoms: list[str] = Field(default_factory=list)
    progression: str | None = None
    behaviours: list[str] = Field(default_factory=list)
    condition_probabilities: dict[str, float] = Field(default_factory=dict)
    spans: list[ExtractedSpanSchema] = Field(default_factory=list)
    text_quality_score: float
    model_confidence: float
    modality_reliability_score: float
    emergency_triage: EmergencyTriageSchema
    warnings: list[str] = Field(default_factory=list)
    model_version: str
