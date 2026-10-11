from datetime import datetime, timezone

from app.features.dogs.application.services.dog_access import DogAccess
from app.features.health_metrics.application.interfaces.repositories.metric_reading_repository import (
    MetricReadingRepositoryProtocol,
)
from app.features.health_metrics.application.queries.get_metric_series.get_metric_series_query import (
    GetMetricSeriesQuery,
)
from app.features.health_metrics.domain.services.build_series import build_series
from app.features.health_metrics.domain.services.history_start import history_start
from app.features.health_metrics.domain.value_objects.metric_series import MetricSeries


class GetMetricSeriesQueryHandler:
    def __init__(self, readings: MetricReadingRepositoryProtocol, access: DogAccess):
        self._readings = readings
        self._access = access

    async def handle(self, query: GetMetricSeriesQuery) -> MetricSeries:
        dog = await self._access.readable(query.actor, query.dog_id)
        now = datetime.now(timezone.utc)
        readings = await self._readings.list_since(
            dog.id, query.metric, history_start(query.time_range, now)
        )
        return build_series(query.metric, query.time_range, readings, now)
