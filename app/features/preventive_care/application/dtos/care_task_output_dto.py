from dataclasses import dataclass
from datetime import datetime

from app.features.preventive_care.domain.enums.care_task_category import CareTaskCategory


@dataclass(frozen=True)
class CareTaskOutputDTO:
    id: str
    dog_id: str
    category: CareTaskCategory
    title: str
    due_date: datetime
    completed: bool
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime | None
    is_overdue: bool
