from dataclasses import dataclass

from app.features.health_metrics.domain.enums.health_metric import HealthMetric


@dataclass(frozen=True)
class MetricTrend:
    """One metric's average over the last 30 days against the 30 days before."""

    metric: HealthMetric
    recent_average: float
    previous_average: float

    @property
    def change_percent(self) -> float:
        if self.previous_average == 0:
            return 0.0
        return (self.recent_average - self.previous_average) / self.previous_average * 100
