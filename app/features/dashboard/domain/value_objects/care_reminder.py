from dataclasses import dataclass
from datetime import datetime

from app.features.dashboard.domain.enums.reminder_kind import ReminderKind


@dataclass(frozen=True)
class CareReminder:
    kind: ReminderKind
    title: str
    due_date: datetime
    is_overdue: bool
