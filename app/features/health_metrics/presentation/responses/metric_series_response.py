from pydantic import BaseModel, ConfigDict

from app.features.health_metrics.domain.enums.health_metric import HealthMetric
from app.features.health_metrics.domain.enums.metric_time_range import MetricTimeRange
from app.features.health_metrics.presentation.responses.metric_point_response import (
    MetricPointResponse,
)


class MetricSeriesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metric: HealthMetric
    range: MetricTimeRange
    points: list[MetricPointResponse]
    baseline_average: float
