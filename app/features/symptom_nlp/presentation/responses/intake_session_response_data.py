from pydantic import BaseModel, Field

from app.features.symptom_nlp.presentation.responses.symptom_parse_response_data import (
    SymptomParseResponseData,
)
from app.features.symptom_nlp.presentation.schemas.emergency_triage_schema import (
    EmergencyTriageSchema,
)


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
