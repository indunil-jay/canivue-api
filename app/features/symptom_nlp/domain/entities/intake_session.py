from dataclasses import dataclass

from app.features.symptom_nlp.domain.value_objects.intake_message import IntakeMessage
from app.features.symptom_nlp.domain.value_objects.symptom_parse_result import SymptomParseResult


@dataclass
class IntakeSession:
    session_id: str
    dog_id: str
    status: str
    turn_count: int
    messages: list[IntakeMessage]
    accumulated_parse: SymptomParseResult
    missing_slots: list[str]
    agent_message: str
    created_at: str
    updated_at: str
    is_complete: bool = False
