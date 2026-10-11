from fastapi import APIRouter, Depends, Form, UploadFile, status

from app.config import settings
from app.core.file_storage import read_upload
from app.core.response import APIResponse
from app.features.assessments.application.use_cases import (
    GetLatestPredictionUseCase,
    GetPredictionUseCase,
    HealthCheckInput,
    ListPredictionsUseCase,
    RecordPredictionOutcomeUseCase,
    RunHealthCheckUseCase,
)
from app.features.assessments.presentation.dependencies import (
    get_get_prediction_use_case,
    get_latest_prediction_use_case,
    get_list_predictions_use_case,
    get_record_prediction_outcome_use_case,
    get_run_health_check_use_case,
)
from app.features.assessments.presentation.schemas import (
    HealthCheckResponse,
    PredictionOutcomeRequest,
    PredictionResponse,
)
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
    use_case: RunHealthCheckUseCase = Depends(get_run_health_check_use_case),
) -> APIResponse[HealthCheckResponse]:
    outcome = await use_case.execute(
        actor,
        HealthCheckInput(
            dog_id=dog_id,
            symptom_text=symptom_text,
            use_sensor_data=use_sensor_data,
            image=await read_upload(image) if image else None,
            image_content_type=image.content_type if image else None,
            max_image_bytes=settings.MAX_UPLOAD_BYTES,
        ),
    )
    return APIResponse(message="Assessment completed", data=HealthCheckResponse.of_outcome(outcome))


@router.get(
    "/{dog_id}/predictions",
    response_model=APIResponse[list[PredictionResponse]],
    summary="List a Dog's prediction history, newest first",
)
async def list_predictions(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    use_case: ListPredictionsUseCase = Depends(get_list_predictions_use_case),
) -> APIResponse[list[PredictionResponse]]:
    predictions = await use_case.execute(actor, dog_id)
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
    use_case: GetLatestPredictionUseCase = Depends(get_latest_prediction_use_case),
) -> APIResponse[PredictionResponse | None]:
    prediction = await use_case.execute(actor, dog_id)
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
    use_case: GetPredictionUseCase = Depends(get_get_prediction_use_case),
) -> APIResponse[HealthCheckResponse]:
    prediction = await use_case.execute(actor, dog_id, prediction_id)
    return APIResponse(
        message="Assessment retrieved successfully", data=HealthCheckResponse.of(prediction)
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
    use_case: RecordPredictionOutcomeUseCase = Depends(get_record_prediction_outcome_use_case),
) -> APIResponse[PredictionResponse]:
    prediction = await use_case.execute(
        actor, dog_id, prediction_id, payload.outcome_note, payload.resolved
    )
    return APIResponse(
        message="Outcome recorded", data=PredictionResponse.model_validate(prediction)
    )
