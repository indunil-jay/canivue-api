from dataclasses import dataclass

from app.features.health_metrics.domain.enums.health_metric import HealthMetric
from app.features.health_metrics.domain.enums.metric_time_range import MetricTimeRange
from app.shared.actor import Actor


@dataclass(frozen=True)
class GetMetricSeriesQuery:
    actor: Actor
    dog_id: str
    metric: HealthMetric
    time_range: MetricTimeRange
