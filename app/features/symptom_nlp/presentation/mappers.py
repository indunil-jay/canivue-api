from app.features.symptom_nlp.application.dtos.intake_session_output_dto import (
    IntakeSessionOutputDTO,
)
from app.features.symptom_nlp.application.dtos.parse_symptom_output_dto import (
    ParseSymptomOutputDTO,
)
from app.features.symptom_nlp.domain.value_objects.emergency_triage_alert import (
    EmergencyTriageAlert,
)
from app.features.symptom_nlp.presentation.responses.intake_session_response_data import (
    IntakeSessionResponseData,
)
from app.features.symptom_nlp.presentation.responses.symptom_parse_response_data import (
    SymptomParseResponseData,
)
from app.features.symptom_nlp.presentation.schemas.body_location_schema import BodyLocationSchema
from app.features.symptom_nlp.presentation.schemas.duration_schema import DurationSchema
from app.features.symptom_nlp.presentation.schemas.emergency_triage_schema import (
    EmergencyTriageSchema,
)
from app.features.symptom_nlp.presentation.schemas.extracted_span_schema import ExtractedSpanSchema


class SymptomNlpPresentationMapper:
    @staticmethod
    def to_emergency_triage_schema(alert: EmergencyTriageAlert) -> EmergencyTriageSchema:
        return EmergencyTriageSchema(
            is_critical=alert.is_critical,
            reason=alert.reason,
            recommendation=alert.recommendation,
        )

    @staticmethod
    def to_symptom_parse_response(dto: ParseSymptomOutputDTO) -> SymptomParseResponseData:
        return SymptomParseResponseData(
            raw_text=dto.raw_text,
            symptoms=dto.symptoms,
            negated_symptoms=dto.negated_symptoms,
            body_locations=[
                BodyLocationSchema(part=loc.part, side=loc.side) for loc in dto.body_locations
            ],
            duration=(
                DurationSchema(value=dto.duration.value, unit=dto.duration.unit)
                if dto.duration
                else None
            ),
            frequency=dto.frequency,
            severity_cues=dto.severity_cues,
            new_symptoms=dto.new_symptoms,
            progression=dto.progression,
            behaviours=dto.behaviours,
            condition_probabilities=dto.condition_probabilities,
            spans=[
                ExtractedSpanSchema(
                    entity=span.entity,
                    text=span.text,
                    start=span.start,
                    end=span.end,
                    negated=span.negated,
                )
                for span in dto.spans
            ],
            text_quality_score=dto.text_quality_score,
            model_confidence=dto.model_confidence,
            modality_reliability_score=dto.modality_reliability_score,
            emergency_triage=SymptomNlpPresentationMapper.to_emergency_triage_schema(
                dto.emergency_triage
            ),
            warnings=dto.warnings,
            model_version=dto.model_version,
        )

    @staticmethod
    def to_intake_session_response(dto: IntakeSessionOutputDTO) -> IntakeSessionResponseData:
        return IntakeSessionResponseData(
            session_id=dto.session_id,
            dog_id=dto.dog_id,
            status=dto.status,
            turn_count=dto.turn_count,
            agent_message=dto.agent_message,
            missing_slots=dto.missing_slots,
            current_parse=SymptomNlpPresentationMapper.to_symptom_parse_response(dto.current_parse),
            emergency_triage=SymptomNlpPresentationMapper.to_emergency_triage_schema(
                dto.emergency_triage
            ),
            is_complete=dto.is_complete,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )
