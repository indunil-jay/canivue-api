from dataclasses import dataclass

from app.features.health_metrics.domain.enums.health_metric import HealthMetric
from app.features.health_metrics.domain.enums.metric_time_range import MetricTimeRange
from app.features.health_metrics.domain.value_objects.metric_point import MetricPoint


@dataclass(frozen=True)
class MetricSeries:
    metric: HealthMetric
    range: MetricTimeRange
    points: list[MetricPoint]
    baseline_average: float
