from dataclasses import dataclass

from app.features.vet_portal.application.dtos.recent_message_preview import RecentMessagePreview
from app.features.vet_portal.application.dtos.schedule_entry import ScheduleEntry


@dataclass(frozen=True)
class VetDashboardSummary:
    vet_name: str
    today_schedule: list[ScheduleEntry]
    waiting_consultation_count: int
    critical_alert_count: int
    new_patient_count: int
    recent_messages: list[RecentMessagePreview]
