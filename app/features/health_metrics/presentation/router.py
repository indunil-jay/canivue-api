from fastapi import APIRouter, Depends, Query, status

from app.core.response import APIResponse
from app.features.auth.presentation.dependencies import get_actor
from app.features.health_metrics.application.commands.record_readings.record_readings_command import (
    RecordReadingsCommand,
)
from app.features.health_metrics.application.commands.record_readings.record_readings_command_handler import (
    RecordReadingsCommandHandler,
)
from app.features.health_metrics.application.queries.get_metric_series.get_metric_series_query import (
    GetMetricSeriesQuery,
)
from app.features.health_metrics.application.queries.get_metric_series.get_metric_series_query_handler import (
    GetMetricSeriesQueryHandler,
)
from app.features.health_metrics.domain.enums.health_metric import HealthMetric
from app.features.health_metrics.domain.enums.metric_time_range import MetricTimeRange
from app.features.health_metrics.presentation.dependencies import (
    get_metric_series_query_handler,
    get_record_readings_command_handler,
)
from app.features.health_metrics.presentation.requests.record_readings_request import (
    RecordReadingsRequest,
)
from app.features.health_metrics.presentation.responses.metric_series_response import (
    MetricSeriesResponse,
)
from app.features.health_metrics.presentation.responses.stored_response import StoredResponse
from app.shared.actor import Actor

router = APIRouter()


@router.post(
    "/{dog_id}/metrics/{metric}/readings",
    response_model=APIResponse[StoredResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit readings for one metric",
    description="Units: heartRate bpm, activity steps, sleep hours, temperature °C, "
    "weight kg, hydration ml. A batch is stored whole or not at all.",
)
async def record_readings(
    dog_id: str,
    metric: HealthMetric,
    payload: RecordReadingsRequest,
    actor: Actor = Depends(get_actor),
    handler: RecordReadingsCommandHandler = Depends(get_record_readings_command_handler),
) -> APIResponse[StoredResponse]:
    stored = await handler.handle(
        RecordReadingsCommand(
            actor=actor,
            dog_id=dog_id,
            metric=metric,
            values=[(r.value, r.recorded_at) for r in payload.readings],
        )
    )
    return APIResponse(message="Readings stored", data=StoredResponse(stored=stored))


@router.get(
    "/{dog_id}/metrics/{metric}",
    response_model=APIResponse[MetricSeriesResponse],
    summary="Get a metric series with the Dog's baseline",
    description="daily: hourly points for the last 24 hours. weekly and monthly: daily points "
    "for the last 7 or 30 days. Periods without readings are omitted.",
)
async def get_metric_series(
    dog_id: str,
    metric: HealthMetric,
    time_range: MetricTimeRange = Query(MetricTimeRange.WEEKLY, alias="range"),
    actor: Actor = Depends(get_actor),
    handler: GetMetricSeriesQueryHandler = Depends(get_metric_series_query_handler),
) -> APIResponse[MetricSeriesResponse]:
    series = await handler.handle(
        GetMetricSeriesQuery(actor=actor, dog_id=dog_id, metric=metric, time_range=time_range)
    )
    return APIResponse(
        message="Metric series retrieved successfully",
        data=MetricSeriesResponse.model_validate(series),
    )
