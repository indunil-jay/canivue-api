from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from app.features.health_metrics.domain.entities.metric_reading import MetricReading
from app.features.health_metrics.domain.enums.health_metric import HealthMetric


class MetricReadingRepositoryProtocol(Protocol):
    async def add_many(self, readings: Sequence[MetricReading]) -> None: ...

    async def list_since(
        self, dog_id: str, metric: HealthMetric, since: datetime
    ) -> Sequence[MetricReading]: ...

    async def latest(self, dog_id: str, metric: HealthMetric) -> MetricReading | None: ...
