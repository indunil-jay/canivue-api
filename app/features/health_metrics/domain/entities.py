from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Protocol

from app.core.exceptions import ValidationException
from app.shared.entity import BaseEntity, _utc_now


class HealthMetric(str, Enum):
    HEART_RATE = "heartRate"
    ACTIVITY = "activity"
    SLEEP = "sleep"
    TEMPERATURE = "temperature"
    WEIGHT = "weight"
    HYDRATION = "hydration"


class MetricTimeRange(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


M = HealthMetric

# Steps, sleep hours and water add up over a period; the others are averaged.
CUMULATIVE = {M.ACTIVITY, M.SLEEP, M.HYDRATION}

# How far from the Dog's own baseline a value may sit before it is flagged, as a fraction.
ABNORMAL_DEVIATION = {
    M.HEART_RATE: 0.20,
    M.ACTIVITY: 0.50,
    M.SLEEP: 0.30,
    M.TEMPERATURE: 0.02,
    M.WEIGHT: 0.05,
    M.HYDRATION: 0.40,
}

# Values outside these are measurement errors, not readings (bpm, steps, hours, °C, kg, ml).
PLAUSIBLE_RANGE = {
    M.HEART_RATE: (20, 300),
    M.ACTIVITY: (0, 200_000),
    M.SLEEP: (0, 24),
    M.TEMPERATURE: (30, 45),
    M.WEIGHT: (0.2, 150),
    M.HYDRATION: (0, 20_000),
}

BASELINE_DAYS = 90
# (bucket size, number of buckets) per range.
_WINDOWS = {
    MetricTimeRange.DAILY: (timedelta(hours=1), 24),
    MetricTimeRange.WEEKLY: (timedelta(days=1), 7),
    MetricTimeRange.MONTHLY: (timedelta(days=1), 30),
}


class ImplausibleReadingError(ValidationException):
    def __init__(self, metric: HealthMetric, reason: str) -> None:
        super().__init__(message=f"Reading for {metric.value} rejected: {reason}.")


@dataclass
class MetricReading(BaseEntity):
    dog_id: str = ""
    metric: HealthMetric = M.HEART_RATE
    value: float = 0.0
    recorded_at: datetime = field(default_factory=_utc_now)

    def validate(self, now: datetime) -> None:
        low, high = PLAUSIBLE_RANGE[self.metric]
        if not low <= self.value <= high:
            raise ImplausibleReadingError(self.metric, f"value must be between {low} and {high}")
        if self.recorded_at > now + timedelta(minutes=5):
            raise ImplausibleReadingError(self.metric, "it is dated in the future")


@dataclass(frozen=True)
class MetricPoint:
    date: datetime
    value: float
    is_abnormal: bool = False


@dataclass(frozen=True)
class MetricSeries:
    metric: HealthMetric
    range: MetricTimeRange
    points: list[MetricPoint]
    baseline_average: float


def history_start(time_range: MetricTimeRange, now: datetime) -> datetime:
    """How far back readings are needed to build a series and its baseline."""
    size, count = _WINDOWS[time_range]
    return now - size * count - timedelta(days=BASELINE_DAYS)


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
    size, count = _WINDOWS[time_range]
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


class MetricReadingRepositoryProtocol(Protocol):
    async def add_many(self, readings: Sequence[MetricReading]) -> None: ...

    async def list_since(
        self, dog_id: str, metric: HealthMetric, since: datetime
    ) -> Sequence[MetricReading]: ...

    async def latest(self, dog_id: str, metric: HealthMetric) -> MetricReading | None: ...
