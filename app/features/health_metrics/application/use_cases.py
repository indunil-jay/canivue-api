from collections.abc import Sequence
from datetime import datetime, timezone

from app.features.dogs.application.access import DogAccess
from app.features.health_metrics.domain.entities import (
    HealthMetric,
    MetricReading,
    MetricReadingRepositoryProtocol,
    MetricSeries,
    MetricTimeRange,
    build_series,
    history_start,
)
from app.shared.actor import Actor


class RecordReadingsUseCase:
    def __init__(self, readings: MetricReadingRepositoryProtocol, access: DogAccess):
        self._readings = readings
        self._access = access

    async def execute(
        self,
        actor: Actor,
        dog_id: str,
        metric: HealthMetric,
        values: Sequence[tuple[float, datetime | None]],
    ) -> int:
        dog = await self._access.owned(actor, dog_id)
        now = datetime.now(timezone.utc)
        readings = []
        for value, recorded_at in values:
            when = recorded_at or now
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            reading = MetricReading(dog_id=dog.id, metric=metric, value=value, recorded_at=when)
            reading.validate(now)
            readings.append(reading)
        await self._readings.add_many(readings)
        return len(readings)


class GetMetricSeriesUseCase:
    def __init__(self, readings: MetricReadingRepositoryProtocol, access: DogAccess):
        self._readings = readings
        self._access = access

    async def execute(
        self, actor: Actor, dog_id: str, metric: HealthMetric, time_range: MetricTimeRange
    ) -> MetricSeries:
        dog = await self._access.readable(actor, dog_id)
        now = datetime.now(timezone.utc)
        readings = await self._readings.list_since(dog.id, metric, history_start(time_range, now))
        return build_series(metric, time_range, readings, now)
