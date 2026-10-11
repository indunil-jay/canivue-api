from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.dataclass_repository import DataclassRepository
from app.core.models import UtcDateTime, UuidTimestampMixin
from app.features.health_metrics.domain.entities import (
    HealthMetric,
    MetricReading,
    MetricReadingRepositoryProtocol,
)


class MetricReadingModel(UuidTimestampMixin, Base):
    __tablename__ = "metric_readings"
    __table_args__ = (Index("ix_metric_readings_lookup", "dog_id", "metric", "recorded_at"),)

    dog_id: Mapped[str] = mapped_column(String(36), nullable=False)
    metric: Mapped[str] = mapped_column(String(20), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)


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
