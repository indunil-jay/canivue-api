from fastapi import APIRouter, Depends, status

from app.core.response import APIResponse
from app.features.symptom_nlp.application.commands.complete_intake_session.complete_intake_session_command import (
    CompleteIntakeSessionCommand,
)
from app.features.symptom_nlp.application.commands.complete_intake_session.complete_intake_session_command_handler import (
    CompleteIntakeSessionCommandHandler,
)
from app.features.symptom_nlp.application.commands.conduct_intake_turn.conduct_intake_turn_command import (
    ConductIntakeTurnCommand,
)
from app.features.symptom_nlp.application.commands.conduct_intake_turn.conduct_intake_turn_command_handler import (
    ConductIntakeTurnCommandHandler,
)
from app.features.symptom_nlp.application.commands.parse_symptom_text.parse_symptom_text_command import (
    ParseSymptomTextCommand,
)
from app.features.symptom_nlp.application.commands.parse_symptom_text.parse_symptom_text_command_handler import (
    ParseSymptomTextCommandHandler,
)
from app.features.symptom_nlp.application.commands.start_intake_session.start_intake_session_command import (
    StartIntakeSessionCommand,
)
from app.features.symptom_nlp.application.commands.start_intake_session.start_intake_session_command_handler import (
    StartIntakeSessionCommandHandler,
)
from app.features.symptom_nlp.presentation.dependencies import (
    get_complete_intake_session_command_handler,
    get_conduct_intake_turn_command_handler,
    get_parse_symptom_text_command_handler,
    get_start_intake_session_command_handler,
)
from app.features.symptom_nlp.presentation.mappers import SymptomNlpPresentationMapper
from app.features.symptom_nlp.presentation.requests.intake_turn_request import IntakeTurnRequest
from app.features.symptom_nlp.presentation.requests.start_intake_request import StartIntakeRequest
from app.features.symptom_nlp.presentation.requests.symptom_parse_request import SymptomParseRequest
from app.features.symptom_nlp.presentation.responses.intake_session_response_data import (
    IntakeSessionResponseData,
)
from app.features.symptom_nlp.presentation.responses.symptom_parse_response_data import (
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
    handler: ParseSymptomTextCommandHandler = Depends(get_parse_symptom_text_command_handler),
) -> APIResponse[SymptomParseResponseData]:
    result = await handler.handle(ParseSymptomTextCommand(text=payload.text))
    data = SymptomNlpPresentationMapper.to_symptom_parse_response(result)

    return APIResponse(
        success=True,
        message="Symptom text parsed successfully",
        data=data,
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
    handler: StartIntakeSessionCommandHandler = Depends(get_start_intake_session_command_handler),
) -> APIResponse[IntakeSessionResponseData]:
    session_dto = await handler.handle(
        StartIntakeSessionCommand(dog_id=payload.dog_id, initial_text=payload.initial_text)
    )

    data = SymptomNlpPresentationMapper.to_intake_session_response(session_dto)

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
    handler: ConductIntakeTurnCommandHandler = Depends(get_conduct_intake_turn_command_handler),
) -> APIResponse[IntakeSessionResponseData]:
    session_dto = await handler.handle(
        ConductIntakeTurnCommand(session_id=session_id, message=payload.message)
    )

    data = SymptomNlpPresentationMapper.to_intake_session_response(session_dto)

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
    handler: CompleteIntakeSessionCommandHandler = Depends(
        get_complete_intake_session_command_handler
    ),
) -> APIResponse[SymptomParseResponseData]:
    result_dto = await handler.handle(CompleteIntakeSessionCommand(session_id=session_id))
    data = SymptomNlpPresentationMapper.to_symptom_parse_response(result_dto)

    return APIResponse(
        success=True,
        message="Intake session finalized successfully",
        data=data,
    )
