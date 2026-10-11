from fastapi import APIRouter, Depends, Form, UploadFile, status

from app.config import settings
from app.core.file_storage import read_upload
from app.core.response import APIResponse
from app.features.assessments.application.commands.record_prediction_outcome.record_prediction_outcome_command import (
    RecordPredictionOutcomeCommand,
)
from app.features.assessments.application.commands.record_prediction_outcome.record_prediction_outcome_command_handler import (
    RecordPredictionOutcomeCommandHandler,
)
from app.features.assessments.application.commands.run_health_check.run_health_check_command import (
    RunHealthCheckCommand,
)
from app.features.assessments.application.commands.run_health_check.run_health_check_command_handler import (
    RunHealthCheckCommandHandler,
)
from app.features.assessments.application.dtos.health_check_input import HealthCheckInput
from app.features.assessments.application.queries.get_latest_prediction.get_latest_prediction_query import (
    GetLatestPredictionQuery,
)
from app.features.assessments.application.queries.get_latest_prediction.get_latest_prediction_query_handler import (
    GetLatestPredictionQueryHandler,
)
from app.features.assessments.application.queries.get_prediction.get_prediction_query import (
    GetPredictionQuery,
)
from app.features.assessments.application.queries.get_prediction.get_prediction_query_handler import (
    GetPredictionQueryHandler,
)
from app.features.assessments.application.queries.list_predictions.list_predictions_query import (
    ListPredictionsQuery,
)
from app.features.assessments.application.queries.list_predictions.list_predictions_query_handler import (
    ListPredictionsQueryHandler,
)
from app.features.assessments.presentation.dependencies import (
    get_latest_prediction_query_handler,
    get_list_predictions_query_handler,
    get_prediction_query_handler,
    get_record_prediction_outcome_command_handler,
    get_run_health_check_command_handler,
)
from app.features.assessments.presentation.mappers import AssessmentsPresentationMapper
from app.features.assessments.presentation.requests.prediction_outcome_request import (
    PredictionOutcomeRequest,
)
from app.features.assessments.presentation.responses.health_check_response import (
    HealthCheckResponse,
)
from app.features.assessments.presentation.responses.prediction_response import PredictionResponse
from app.features.auth.presentation.dependencies import get_actor
from app.shared.actor import Actor

router = APIRouter()


@router.post(
    "/{dog_id}/health-checks",
    response_model=APIResponse[HealthCheckResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Run an Assessment for a Dog",
    description="Multipart form. Send any combination of a photo (`image`), a symptom "
    "description (`symptom_text`) and `use_sensor_data=true`; at least one must yield "
    "evidence. The result is decision support, not a diagnosis, and is stored as a prediction.",
)
async def run_health_check(
    dog_id: str,
    image: UploadFile | None = None,
    symptom_text: str = Form("", max_length=4000),
    use_sensor_data: bool = Form(False),
    actor: Actor = Depends(get_actor),
    handler: RunHealthCheckCommandHandler = Depends(get_run_health_check_command_handler),
) -> APIResponse[HealthCheckResponse]:
    outcome = await handler.handle(
        RunHealthCheckCommand(
            actor=actor,
            data=HealthCheckInput(
                dog_id=dog_id,
                symptom_text=symptom_text,
                use_sensor_data=use_sensor_data,
                image=await read_upload(image) if image else None,
                image_content_type=image.content_type if image else None,
                max_image_bytes=settings.MAX_UPLOAD_BYTES,
            ),
        )
    )
    return APIResponse(
        message="Assessment completed",
        data=AssessmentsPresentationMapper.to_health_check_response_from_outcome(outcome),
    )


@router.get(
    "/{dog_id}/predictions",
    response_model=APIResponse[list[PredictionResponse]],
    summary="List a Dog's prediction history, newest first",
)
async def list_predictions(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    handler: ListPredictionsQueryHandler = Depends(get_list_predictions_query_handler),
) -> APIResponse[list[PredictionResponse]]:
    predictions = await handler.handle(ListPredictionsQuery(actor=actor, dog_id=dog_id))
    return APIResponse(
        message="Predictions retrieved successfully",
        data=[PredictionResponse.model_validate(p) for p in predictions],
    )


@router.get(
    "/{dog_id}/predictions/latest",
    response_model=APIResponse[PredictionResponse | None],
    summary="Get a Dog's latest unresolved prediction, or null when there is none",
)
async def get_latest_prediction(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    handler: GetLatestPredictionQueryHandler = Depends(get_latest_prediction_query_handler),
) -> APIResponse[PredictionResponse | None]:
    prediction = await handler.handle(GetLatestPredictionQuery(actor=actor, dog_id=dog_id))
    return APIResponse(
        message="Latest prediction retrieved successfully",
        data=PredictionResponse.model_validate(prediction) if prediction else None,
    )


@router.get(
    "/{dog_id}/predictions/{prediction_id}",
    response_model=APIResponse[HealthCheckResponse],
    summary="Get the full Assessment behind a prediction",
)
async def get_prediction(
    dog_id: str,
    prediction_id: str,
    actor: Actor = Depends(get_actor),
    handler: GetPredictionQueryHandler = Depends(get_prediction_query_handler),
) -> APIResponse[HealthCheckResponse]:
    prediction = await handler.handle(
        GetPredictionQuery(actor=actor, dog_id=dog_id, prediction_id=prediction_id)
    )
    return APIResponse(
        message="Assessment retrieved successfully",
        data=AssessmentsPresentationMapper.to_health_check_response(prediction),
    )


@router.patch(
    "/{dog_id}/predictions/{prediction_id}/outcome",
    response_model=APIResponse[PredictionResponse],
    summary="Record the follow-up outcome of a prediction (treating veterinarian)",
)
async def record_prediction_outcome(
    dog_id: str,
    prediction_id: str,
    payload: PredictionOutcomeRequest,
    actor: Actor = Depends(get_actor),
    handler: RecordPredictionOutcomeCommandHandler = Depends(
        get_record_prediction_outcome_command_handler
    ),
) -> APIResponse[PredictionResponse]:
    prediction = await handler.handle(
        RecordPredictionOutcomeCommand(
            actor=actor,
            dog_id=dog_id,
            prediction_id=prediction_id,
            outcome_note=payload.outcome_note,
            resolved=payload.resolved,
        )
    )
    return APIResponse(
        message="Outcome recorded", data=PredictionResponse.model_validate(prediction)
    )
