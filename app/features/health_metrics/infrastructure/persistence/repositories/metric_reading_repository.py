from collections.abc import Sequence
from datetime import datetime

from app.core.dataclass_repository import DataclassRepository
from app.features.health_metrics.application.interfaces.repositories.metric_reading_repository import (
    MetricReadingRepositoryProtocol,
)
from app.features.health_metrics.domain.entities.metric_reading import MetricReading
from app.features.health_metrics.domain.enums.health_metric import HealthMetric
from app.features.health_metrics.infrastructure.persistence.models.metric_reading_model import (
    MetricReadingModel,
)


class SqlAlchemyMetricReadingRepository(
    DataclassRepository[MetricReading, MetricReadingModel], MetricReadingRepositoryProtocol
):
    _model_cls = MetricReadingModel
    _entity_cls = MetricReading

    async def add_many(self, readings: Sequence[MetricReading]) -> None:
        self._session.add_all(MetricReadingModel(**self._to_model_dict(r)) for r in readings)
        await self._session.flush()

    async def list_since(
        self, dog_id: str, metric: HealthMetric, since: datetime
    ) -> Sequence[MetricReading]:
        return await self.find(
            MetricReadingModel.dog_id == dog_id,
            MetricReadingModel.metric == metric.value,
            MetricReadingModel.recorded_at >= since,
            order_by=MetricReadingModel.recorded_at,
        )

    async def latest(self, dog_id: str, metric: HealthMetric) -> MetricReading | None:
        return await self.find_one(
            MetricReadingModel.dog_id == dog_id,
            MetricReadingModel.metric == metric.value,
            order_by=MetricReadingModel.recorded_at.desc(),
        )
