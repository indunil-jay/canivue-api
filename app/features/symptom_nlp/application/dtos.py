from dataclasses import dataclass

from app.features.symptom_nlp.domain.entities import (
    BodyLocation,
    DurationEntity,
    EmergencyTriageAlert,
    ExtractedSpan,
    IntakeSession,
    SymptomParseResult,
)


@dataclass
class ParseSymptomInputDTO:
    text: str


@dataclass
class ParseSymptomOutputDTO:
    raw_text: str
    symptoms: list[str]
    negated_symptoms: list[str]
    body_locations: list[BodyLocation]
    duration: DurationEntity | None
    frequency: dict[str, str] | None
    severity_cues: list[str]
    new_symptoms: list[str]
    progression: str | None
    behaviours: list[str]
    condition_probabilities: dict[str, float]
    spans: list[ExtractedSpan]
    text_quality_score: float
    model_confidence: float
    modality_reliability_score: float
    emergency_triage: EmergencyTriageAlert
    warnings: list[str]
    model_version: str

    @classmethod
    def from_entity(cls, entity: SymptomParseResult) -> "ParseSymptomOutputDTO":
        return cls(
            raw_text=entity.raw_text,
            symptoms=entity.symptoms,
            negated_symptoms=entity.negated_symptoms,
            body_locations=entity.body_locations,
            duration=entity.duration,
            frequency=entity.frequency,
            severity_cues=entity.severity_cues,
            new_symptoms=entity.new_symptoms,
            progression=entity.progression,
            behaviours=entity.behaviours,
            condition_probabilities=entity.condition_probabilities,
            spans=entity.spans,
            text_quality_score=entity.text_quality_score,
            model_confidence=entity.model_confidence,
            modality_reliability_score=entity.modality_reliability_score,
            emergency_triage=entity.emergency_triage,
            warnings=entity.warnings,
            model_version=entity.model_version,
        )


@dataclass
class StartIntakeInputDTO:
    dog_id: str
    initial_text: str


@dataclass
class ConductTurnInputDTO:
    session_id: str
    message: str


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

