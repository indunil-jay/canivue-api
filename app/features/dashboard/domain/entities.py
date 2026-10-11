from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol

from app.features.health_metrics.domain.entities import HealthMetric

ACTIVITY_GOAL_STEPS = 8000
HYDRATION_ML_PER_KG = 60


class InsightRisk(str, Enum):
    NORMAL = "normal"
    MONITORING = "monitoring"
    ELEVATED = "elevated"


class ReminderKind(str, Enum):
    VACCINATION = "vaccination"
    MEDICATION = "medication"
    GROOMING = "grooming"
    CHECKUP = "checkup"
    DEWORMING = "deworming"


class DeviceConnectionState(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    NOT_PAIRED = "notPaired"


class TimelineEventType(str, Enum):
    VACCINATION = "vaccination"
    MEDICATION = "medication"
    WEIGHT_CHANGE = "weightChange"
    DIAGNOSIS = "diagnosis"
    APPOINTMENT = "appointment"
    AI_PREDICTION = "aiPrediction"
    HEALTH_ALERT = "healthAlert"
    SENSOR_EVENT = "sensorEvent"


class TrendDirection(str, Enum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


@dataclass(frozen=True)
class VitalsSnapshot:
    heart_rate_bpm: int | None
    temperature_c: float | None
    activity_steps_today: int
    activity_goal_steps: int
    sleep_hours_last_night: float | None
    hydration_ml: int
    hydration_goal_ml: int
    weight_kg: float


@dataclass(frozen=True)
class AiInsight:
    headline: str
    detail: str
    risk: InsightRisk = InsightRisk.NORMAL


@dataclass(frozen=True)
class CareReminder:
    kind: ReminderKind
    title: str
    due_date: datetime
    is_overdue: bool


@dataclass(frozen=True)
class UpcomingAppointment:
    vet_name: str
    clinic: str
    time: datetime
    is_video_call: bool


@dataclass(frozen=True)
class DeviceStatus:
    state: DeviceConnectionState
    device_name: str
    battery_percent: int | None
    last_synced_at: datetime | None


@dataclass(frozen=True)
class DashboardSummary:
    health_score: int | None
    vitals: VitalsSnapshot
    insight: AiInsight
    reminders: list[CareReminder]
    appointment: UpcomingAppointment | None
    device: DeviceStatus


@dataclass(frozen=True)
class HealthTimelineEvent:
    type: TimelineEventType
    title: str
    description: str
    date: datetime


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


@dataclass(frozen=True)
class HealthInsight:
    headline: str
    detail: str
    direction: TrendDirection
    is_positive: bool = True


class InsightEngineProtocol(Protocol):
    """Turns metric trends into plain-language statements for an owner."""

    async def summarise(
        self, dog_name: str, trends: Sequence[MetricTrend]
    ) -> list[HealthInsight]: ...


def health_score(
    latest_risk_percent: float | None, abnormal_vitals: int, has_data: bool
) -> int | None:
    """100 minus half the latest predicted risk and 5 per vital currently off baseline.

    None when there is nothing to judge by: no readings and no prediction.
    """
    if not has_data:
        return None
    score = 100 - (latest_risk_percent or 0) * 0.5 - 5 * abnormal_vitals
    return max(0, min(100, round(score)))
