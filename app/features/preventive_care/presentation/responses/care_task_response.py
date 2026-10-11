from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.features.preventive_care.domain.enums.care_task_category import CareTaskCategory


class CareTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    dog_id: str
    category: CareTaskCategory
    title: str
    due_date: datetime
    completed: bool
    completed_at: datetime | None
    is_overdue: bool
