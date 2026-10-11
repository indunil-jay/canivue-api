from dataclasses import dataclass, field
from datetime import datetime

from app.features.preventive_care.domain.enums.care_task_category import CareTaskCategory
from app.shared.entity import BaseEntity, _utc_now


@dataclass
class CareTask(BaseEntity):
    dog_id: str = ""
    category: CareTaskCategory = CareTaskCategory.VACCINATION
    title: str = ""
    due_date: datetime = field(default_factory=_utc_now)
    completed: bool = False
    completed_at: datetime | None = None

    @property
    def is_overdue(self) -> bool:
        return not self.completed and self.due_date < _utc_now()

    def complete(self) -> None:
        if not self.completed:
            self.completed = True
            self.completed_at = _utc_now()
