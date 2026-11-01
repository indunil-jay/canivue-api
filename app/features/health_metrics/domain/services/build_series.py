from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime, timedelta

from app.features.health_metrics.domain.constants import (
    ABNORMAL_DEVIATION,
    CUMULATIVE,
    RANGE_WINDOWS,
)
from app.features.health_metrics.domain.entities.metric_reading import MetricReading
from app.features.health_metrics.domain.enums.health_metric import HealthMetric
from app.features.health_metrics.domain.enums.metric_time_range import MetricTimeRange
from app.features.health_metrics.domain.value_objects.metric_point import MetricPoint
from app.features.health_metrics.domain.value_objects.metric_series import MetricSeries


def _bucket_start(moment: datetime, size: timedelta) -> datetime:
    if size >= timedelta(days=1):
        return moment.replace(hour=0, minute=0, second=0, microsecond=0)
    return moment.replace(minute=0, second=0, microsecond=0)


def build_series(
    metric: HealthMetric,
    time_range: MetricTimeRange,
    readings: Sequence[MetricReading],
    now: datetime,
) -> MetricSeries:
    """Buckets readings over the range and flags buckets far from the Dog's own baseline.

    The baseline is the average bucket over the 90 days before the window; with no earlier
    history it falls back to the window itself. Buckets with no readings are left out
    rather than reported as zero.
    """
    size, count = RANGE_WINDOWS[time_range]
    window_start = _bucket_start(now, size) - size * (count - 1)

    buckets: dict[datetime, list[float]] = defaultdict(list)
    for reading in readings:
        buckets[_bucket_start(reading.recorded_at, size)].append(reading.value)
    combine = sum if metric in CUMULATIVE else (lambda values: sum(values) / len(values))
    totals = {start: combine(values) for start, values in buckets.items()}

    in_window = {s: v for s, v in totals.items() if s >= window_start}
    earlier = [v for s, v in totals.items() if s < window_start]
    basis = earlier or list(in_window.values())
    baseline = sum(basis) / len(basis) if basis else 0.0

    tolerance = ABNORMAL_DEVIATION[metric]
    points = [
        MetricPoint(
            date=start,
            value=round(value, 2),
            is_abnormal=baseline > 0 and abs(value - baseline) / baseline > tolerance,
        )
        for start, value in sorted(in_window.items())
    ]
    return MetricSeries(metric, time_range, points, round(baseline, 2))
