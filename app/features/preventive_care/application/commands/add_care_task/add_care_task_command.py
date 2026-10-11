from dataclasses import dataclass
from datetime import datetime

from app.features.preventive_care.domain.enums.care_task_category import CareTaskCategory
from app.shared.actor import Actor


@dataclass(frozen=True)
class AddCareTaskCommand:
    actor: Actor
    dog_id: str
    category: CareTaskCategory
    title: str
    due_date: datetime
