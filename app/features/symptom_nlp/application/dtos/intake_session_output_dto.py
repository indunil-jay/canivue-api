from dataclasses import dataclass

from app.features.symptom_nlp.application.dtos.parse_symptom_output_dto import ParseSymptomOutputDTO
from app.features.symptom_nlp.domain.entities.intake_session import IntakeSession
from app.features.symptom_nlp.domain.value_objects.emergency_triage_alert import (
    EmergencyTriageAlert,
)


@dataclass
class IntakeSessionOutputDTO:
    session_id: str
    dog_id: str
    status: str
    turn_count: int
    agent_message: str
    missing_slots: list[str]
    current_parse: ParseSymptomOutputDTO
    emergency_triage: EmergencyTriageAlert
    is_complete: bool
    created_at: str
    updated_at: str

    @classmethod
    def from_entity(cls, entity: "IntakeSession") -> "IntakeSessionOutputDTO":
        return cls(
            session_id=entity.session_id,
            dog_id=entity.dog_id,
            status=entity.status,
            turn_count=entity.turn_count,
            agent_message=entity.agent_message,
            missing_slots=entity.missing_slots,
            current_parse=ParseSymptomOutputDTO.from_entity(entity.accumulated_parse),
            emergency_triage=entity.accumulated_parse.emergency_triage,
            is_complete=entity.is_complete,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
