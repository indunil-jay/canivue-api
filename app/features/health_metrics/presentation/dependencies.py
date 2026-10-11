from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.features.dogs.application.services.dog_access import DogAccess
from app.features.dogs.presentation.dependencies import get_dog_access
from app.features.health_metrics.application.commands.record_readings.record_readings_command_handler import (
    RecordReadingsCommandHandler,
)
from app.features.health_metrics.application.interfaces.repositories.metric_reading_repository import (
    MetricReadingRepositoryProtocol,
)
from app.features.health_metrics.application.queries.get_metric_series.get_metric_series_query_handler import (
    GetMetricSeriesQueryHandler,
)
from app.features.health_metrics.infrastructure.persistence.repositories.metric_reading_repository import (
    SqlAlchemyMetricReadingRepository,
)


def get_metric_reading_repository(
    session: AsyncSession = Depends(get_db_session),
) -> MetricReadingRepositoryProtocol:
    return SqlAlchemyMetricReadingRepository(session=session)


def get_record_readings_command_handler(
    readings: MetricReadingRepositoryProtocol = Depends(get_metric_reading_repository),
    access: DogAccess = Depends(get_dog_access),
) -> RecordReadingsCommandHandler:
    return RecordReadingsCommandHandler(readings, access)


def get_metric_series_query_handler(
    readings: MetricReadingRepositoryProtocol = Depends(get_metric_reading_repository),
    access: DogAccess = Depends(get_dog_access),
) -> GetMetricSeriesQueryHandler:
    return GetMetricSeriesQueryHandler(readings, access)
