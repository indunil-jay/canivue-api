from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.features.dashboard.domain.enums.reminder_kind import ReminderKind


class CareReminderSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kind: ReminderKind
    title: str
    due_date: datetime
    is_overdue: bool
