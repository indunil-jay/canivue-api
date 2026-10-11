from datetime import datetime, timedelta

from app.features.health_metrics.domain.constants import BASELINE_DAYS, RANGE_WINDOWS
from app.features.health_metrics.domain.enums.metric_time_range import MetricTimeRange


def history_start(time_range: MetricTimeRange, now: datetime) -> datetime:
    """How far back readings are needed to build a series and its baseline."""
    size, count = RANGE_WINDOWS[time_range]
    return now - size * count - timedelta(days=BASELINE_DAYS)
