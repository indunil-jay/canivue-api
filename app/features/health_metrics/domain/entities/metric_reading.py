from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.features.health_metrics.domain.constants import PLAUSIBLE_RANGE
from app.features.health_metrics.domain.enums.health_metric import HealthMetric
from app.features.health_metrics.domain.exceptions import ImplausibleReadingError
from app.shared.entity import BaseEntity, _utc_now


@dataclass
class MetricReading(BaseEntity):
    dog_id: str = ""
    metric: HealthMetric = HealthMetric.HEART_RATE
    value: float = 0.0
    recorded_at: datetime = field(default_factory=_utc_now)

    def validate(self, now: datetime) -> None:
        low, high = PLAUSIBLE_RANGE[self.metric]
        if not low <= self.value <= high:
            raise ImplausibleReadingError(self.metric, f"value must be between {low} and {high}")
        if self.recorded_at > now + timedelta(minutes=5):
            raise ImplausibleReadingError(self.metric, "it is dated in the future")
