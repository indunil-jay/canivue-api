from app.core.exceptions import ValidationException
from app.features.health_metrics.domain.enums.health_metric import HealthMetric


class ImplausibleReadingError(ValidationException):
    def __init__(self, metric: HealthMetric, reason: str) -> None:
        super().__init__(message=f"Reading for {metric.value} rejected: {reason}.")
