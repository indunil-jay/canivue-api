from pydantic import BaseModel, ConfigDict, Field

from app.features.dashboard.presentation.schemas.ai_insight_schema import AiInsightSchema
from app.features.dashboard.presentation.schemas.care_reminder_schema import CareReminderSchema
from app.features.dashboard.presentation.schemas.device_status_schema import DeviceStatusSchema
from app.features.dashboard.presentation.schemas.upcoming_appointment_schema import (
    UpcomingAppointmentSchema,
)
from app.features.dashboard.presentation.schemas.vitals_snapshot_schema import VitalsSnapshotSchema


class DashboardSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    health_score: int | None = Field(
        ..., description="0-100, or null when the Dog has no readings and no prediction yet"
    )
    vitals: VitalsSnapshotSchema
    insight: AiInsightSchema
    reminders: list[CareReminderSchema]
    appointment: UpcomingAppointmentSchema | None
    device: DeviceStatusSchema
