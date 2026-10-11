from dataclasses import dataclass

from app.features.dashboard.domain.value_objects.ai_insight import AiInsight
from app.features.dashboard.domain.value_objects.care_reminder import CareReminder
from app.features.dashboard.domain.value_objects.device_status import DeviceStatus
from app.features.dashboard.domain.value_objects.upcoming_appointment import UpcomingAppointment
from app.features.dashboard.domain.value_objects.vitals_snapshot import VitalsSnapshot


@dataclass(frozen=True)
class DashboardSummary:
    health_score: int | None
    vitals: VitalsSnapshot
    insight: AiInsight
    reminders: list[CareReminder]
    appointment: UpcomingAppointment | None
    device: DeviceStatus
