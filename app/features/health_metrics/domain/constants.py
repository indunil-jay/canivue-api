from datetime import timedelta

from app.features.health_metrics.domain.enums.health_metric import HealthMetric
from app.features.health_metrics.domain.enums.metric_time_range import MetricTimeRange

# Steps, sleep hours and water add up over a period; the others are averaged.
CUMULATIVE = {HealthMetric.ACTIVITY, HealthMetric.SLEEP, HealthMetric.HYDRATION}

# How far from the Dog's own baseline a value may sit before it is flagged, as a fraction.
ABNORMAL_DEVIATION = {
    HealthMetric.HEART_RATE: 0.20,
    HealthMetric.ACTIVITY: 0.50,
    HealthMetric.SLEEP: 0.30,
    HealthMetric.TEMPERATURE: 0.02,
    HealthMetric.WEIGHT: 0.05,
    HealthMetric.HYDRATION: 0.40,
}

# Values outside these are measurement errors, not readings (bpm, steps, hours, °C, kg, ml).
PLAUSIBLE_RANGE = {
    HealthMetric.HEART_RATE: (20, 300),
    HealthMetric.ACTIVITY: (0, 200_000),
    HealthMetric.SLEEP: (0, 24),
    HealthMetric.TEMPERATURE: (30, 45),
    HealthMetric.WEIGHT: (0.2, 150),
    HealthMetric.HYDRATION: (0, 20_000),
}

BASELINE_DAYS = 90

# (bucket size, number of buckets) per range.
RANGE_WINDOWS = {
    MetricTimeRange.DAILY: (timedelta(hours=1), 24),
    MetricTimeRange.WEEKLY: (timedelta(days=1), 7),
    MetricTimeRange.MONTHLY: (timedelta(days=1), 30),
}
