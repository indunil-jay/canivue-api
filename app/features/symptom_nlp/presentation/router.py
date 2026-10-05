from fastapi import APIRouter, Depends, status

from app.core.response import APIResponse
from app.features.symptom_nlp.application.dtos import (
    ConductTurnInputDTO,
    ParseSymptomInputDTO,
    StartIntakeInputDTO,
)
from app.features.symptom_nlp.application.use_cases import (
    CompleteIntakeSessionUseCase,
    ConductIntakeTurnUseCase,
    ParseSymptomTextUseCase,
    StartIntakeSessionUseCase,
)
from app.features.symptom_nlp.presentation.dependencies import (
    get_complete_intake_session_use_case,
    get_conduct_intake_turn_use_case,
    get_parse_symptom_use_case,
    get_start_intake_use_case,
)
from app.features.symptom_nlp.presentation.schemas import (
    BodyLocationSchema,
    DurationSchema,
    EmergencyTriageSchema,
    ExtractedSpanSchema,
    IntakeSessionResponseData,
    IntakeTurnRequest,
    StartIntakeRequest,
    SymptomParseRequest,
    SymptomParseResponseData,
)

router = APIRouter()



@router.post(
    "/parse",
    response_model=APIResponse[SymptomParseResponseData],
    status_code=status.HTTP_200_OK,
    summary="Parse informal symptom text into structured evidence",
    description=(
        "Translates freeform dog owner symptom text into normalized clinical features, "
        "calibrated condition probabilities, text-quality scores, and emergency triage alerts."
    ),
)
async def parse_symptoms(
    payload: SymptomParseRequest,
    use_case: ParseSymptomTextUseCase = Depends(get_parse_symptom_use_case),
) -> APIResponse[SymptomParseResponseData]:
    dto = ParseSymptomInputDTO(text=payload.text)
    result = await use_case.execute(dto)

    data = SymptomParseResponseData(
        raw_text=result.raw_text,
        symptoms=result.symptoms,
        negated_symptoms=result.negated_symptoms,
        body_locations=[
            BodyLocationSchema(part=loc.part, side=loc.side) for loc in result.body_locations
        ],
        duration=(
            DurationSchema(value=result.duration.value, unit=result.duration.unit)
            if result.duration
            else None
        ),
        frequency=result.frequency,
        severity_cues=result.severity_cues,
        new_symptoms=result.new_symptoms,
        progression=result.progression,
        behaviours=result.behaviours,
        condition_probabilities=result.condition_probabilities,
        spans=[
            ExtractedSpanSchema(
                entity=span.entity,
                text=span.text,
                start=span.start,
                end=span.end,
                negated=span.negated,
            )
            for span in result.spans
        ],
        text_quality_score=result.text_quality_score,
        model_confidence=result.model_confidence,
        modality_reliability_score=result.modality_reliability_score,
        emergency_triage=EmergencyTriageSchema(
            is_critical=result.emergency_triage.is_critical,
            reason=result.emergency_triage.reason,
            recommendation=result.emergency_triage.recommendation,
        ),
        warnings=result.warnings,
        model_version=result.model_version,
    )

    return APIResponse(
        success=True,
        message="Symptom text parsed successfully",
        data=data,
    )


def _dto_to_parse_response_data(result) -> SymptomParseResponseData:
    return SymptomParseResponseData(
        raw_text=result.raw_text,
        symptoms=result.symptoms,
        negated_symptoms=result.negated_symptoms,
        body_locations=[
            BodyLocationSchema(part=loc.part, side=loc.side) for loc in result.body_locations
        ],
        duration=(
            DurationSchema(value=result.duration.value, unit=result.duration.unit)
            if result.duration
            else None
        ),
        frequency=result.frequency,
        severity_cues=result.severity_cues,
        new_symptoms=result.new_symptoms,
        progression=result.progression,
        behaviours=result.behaviours,
        condition_probabilities=result.condition_probabilities,
        spans=[
            ExtractedSpanSchema(
                entity=span.entity,
                text=span.text,
                start=span.start,
                end=span.end,
                negated=span.negated,
            )
            for span in result.spans
        ],
        text_quality_score=result.text_quality_score,
        model_confidence=result.model_confidence,
        modality_reliability_score=result.modality_reliability_score,
        emergency_triage=EmergencyTriageSchema(
            is_critical=result.emergency_triage.is_critical,
            reason=result.emergency_triage.reason,
            recommendation=result.emergency_triage.recommendation,
        ),
        warnings=result.warnings,
        model_version=result.model_version,
    )


@router.post(
    "/intake/sessions",
    response_model=APIResponse[IntakeSessionResponseData],
    status_code=status.HTTP_200_OK,
    summary="Initialize multi-turn canine symptom intake session",
    description="Starts an interactive consultation session for a dog, extracting symptoms and identifying missing clinical slots.",
)
async def start_intake_session(
    payload: StartIntakeRequest,
    use_case: StartIntakeSessionUseCase = Depends(get_start_intake_use_case),
) -> APIResponse[IntakeSessionResponseData]:
    dto = StartIntakeInputDTO(dog_id=payload.dog_id, initial_text=payload.initial_text)
    session_dto = await use_case.execute(dto)

    data = IntakeSessionResponseData(
        session_id=session_dto.session_id,
        dog_id=session_dto.dog_id,
        status=session_dto.status,
        turn_count=session_dto.turn_count,
        agent_message=session_dto.agent_message,
        missing_slots=session_dto.missing_slots,
        current_parse=_dto_to_parse_response_data(session_dto.current_parse),
        emergency_triage=EmergencyTriageSchema(
            is_critical=session_dto.emergency_triage.is_critical,
            reason=session_dto.emergency_triage.reason,
            recommendation=session_dto.emergency_triage.recommendation,
        ),
        is_complete=session_dto.is_complete,
        created_at=session_dto.created_at,
        updated_at=session_dto.updated_at,
    )

    return APIResponse(
        success=True,
        message="Intake session initialized successfully",
        data=data,
    )


@router.post(
    "/intake/sessions/{session_id}/turns",
    response_model=APIResponse[IntakeSessionResponseData],
    status_code=status.HTTP_200_OK,
    summary="Submit follow-up message to intake session",
    description="Processes owner follow-up input, updates accumulated clinical context, and returns next agent question.",
)
async def conduct_intake_turn(
    session_id: str,
    payload: IntakeTurnRequest,
    use_case: ConductIntakeTurnUseCase = Depends(get_conduct_intake_turn_use_case),
) -> APIResponse[IntakeSessionResponseData]:
    dto = ConductTurnInputDTO(session_id=session_id, message=payload.message)
    session_dto = await use_case.execute(dto)

    data = IntakeSessionResponseData(
        session_id=session_dto.session_id,
        dog_id=session_dto.dog_id,
        status=session_dto.status,
        turn_count=session_dto.turn_count,
        agent_message=session_dto.agent_message,
        missing_slots=session_dto.missing_slots,
        current_parse=_dto_to_parse_response_data(session_dto.current_parse),
        emergency_triage=EmergencyTriageSchema(
            is_critical=session_dto.emergency_triage.is_critical,
            reason=session_dto.emergency_triage.reason,
            recommendation=session_dto.emergency_triage.recommendation,
        ),
        is_complete=session_dto.is_complete,
        created_at=session_dto.created_at,
        updated_at=session_dto.updated_at,
    )

    return APIResponse(
        success=True,
        message="Intake turn processed successfully",
        data=data,
    )


@router.post(
    "/intake/sessions/{session_id}/complete",
    response_model=APIResponse[SymptomParseResponseData],
    status_code=status.HTTP_200_OK,
    summary="Finalize canine intake consultation",
    description="Marks intake session as complete and generates standardized SymptomParseResult evidence for multimodal fusion.",
)
async def complete_intake_session(
    session_id: str,
    use_case: CompleteIntakeSessionUseCase = Depends(get_complete_intake_session_use_case),
) -> APIResponse[SymptomParseResponseData]:
    result_dto = await use_case.execute(session_id=session_id)
    data = _dto_to_parse_response_data(result_dto)

    return APIResponse(
        success=True,
        message="Intake session finalized successfully",
        data=data,
    )



