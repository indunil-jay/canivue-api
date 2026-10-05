
from pydantic import BaseModel, Field


class SymptomParseRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        description="Dog owner's informal, natural language symptom description",
        examples=["My dog has been scratching its left ear for three days and it is becoming red."],
    )


class BodyLocationSchema(BaseModel):
    part: str
    side: str | None = None


class DurationSchema(BaseModel):
    value: int
    unit: str


class ExtractedSpanSchema(BaseModel):
    entity: str
    text: str
    start: int
    end: int
    negated: bool = False


class EmergencyTriageSchema(BaseModel):
    is_critical: bool = False
    reason: str | None = None
    recommendation: str | None = None


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


class StartIntakeRequest(BaseModel):
    dog_id: str = Field(..., description="Unique canine identifier")
    initial_text: str = Field(..., min_length=1, description="Initial symptom text reported by dog owner")


class IntakeTurnRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Follow-up response or clarification from dog owner")


class IntakeSessionResponseData(BaseModel):
    session_id: str
    dog_id: str
    status: str
    turn_count: int
    agent_message: str
    missing_slots: list[str] = Field(default_factory=list)
    current_parse: SymptomParseResponseData
    emergency_triage: EmergencyTriageSchema
    is_complete: bool
    created_at: str
    updated_at: str

