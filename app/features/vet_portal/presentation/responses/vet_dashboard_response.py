from pydantic import BaseModel, ConfigDict

from app.features.vet_portal.presentation.responses.recent_message_preview_response import (
    RecentMessagePreviewResponse,
)
from app.features.vet_portal.presentation.responses.schedule_entry_response import (
    ScheduleEntryResponse,
)


class VetDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vet_name: str
    today_schedule: list[ScheduleEntryResponse]
    waiting_consultation_count: int
    critical_alert_count: int
    new_patient_count: int
    recent_messages: list[RecentMessagePreviewResponse]
