from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.response import APIResponse
from app.features.auth.presentation.dependencies import get_actor
from app.features.dogs.application.access import DogAccess
from app.features.dogs.presentation.dependencies import get_dog_access
from app.features.health_metrics.application.use_cases import (
    GetMetricSeriesUseCase,
    RecordReadingsUseCase,
)
from app.features.health_metrics.domain.entities import (
    HealthMetric,
    MetricReadingRepositoryProtocol,
    MetricTimeRange,
)
from app.features.health_metrics.infrastructure.persistence.repositories import (
    SqlAlchemyMetricReadingRepository,
)
from app.shared.actor import Actor

router = APIRouter()


class ReadingRequest(BaseModel):
    value: float
    recorded_at: datetime | None = Field(None, description="Defaults to now; UTC if no offset")


class RecordReadingsRequest(BaseModel):
    readings: list[ReadingRequest] = Field(..., min_length=1, max_length=1000)


class StoredResponse(BaseModel):
    stored: int


class MetricPointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: datetime
    value: float
    is_abnormal: bool


class MetricSeriesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metric: HealthMetric
    range: MetricTimeRange
    points: list[MetricPointResponse]
    baseline_average: float


def get_metric_reading_repository(
    session: AsyncSession = Depends(get_db_session),
) -> MetricReadingRepositoryProtocol:
    return SqlAlchemyMetricReadingRepository(session=session)


def get_record_readings_use_case(
    readings: MetricReadingRepositoryProtocol = Depends(get_metric_reading_repository),
    access: DogAccess = Depends(get_dog_access),
) -> RecordReadingsUseCase:
    return RecordReadingsUseCase(readings, access)


def get_metric_series_use_case(
    readings: MetricReadingRepositoryProtocol = Depends(get_metric_reading_repository),
    access: DogAccess = Depends(get_dog_access),
) -> GetMetricSeriesUseCase:
    return GetMetricSeriesUseCase(readings, access)


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
    use_case: RecordReadingsUseCase = Depends(get_record_readings_use_case),
) -> APIResponse[StoredResponse]:
    stored = await use_case.execute(
        actor, dog_id, metric, [(r.value, r.recorded_at) for r in payload.readings]
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
    use_case: GetMetricSeriesUseCase = Depends(get_metric_series_use_case),
) -> APIResponse[MetricSeriesResponse]:
    series = await use_case.execute(actor, dog_id, metric, time_range)
    return APIResponse(
        message="Metric series retrieved successfully",
        data=MetricSeriesResponse.model_validate(series),
    )
