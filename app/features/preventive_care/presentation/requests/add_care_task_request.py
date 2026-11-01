from datetime import datetime

from pydantic import BaseModel, Field

from app.features.preventive_care.domain.enums.care_task_category import CareTaskCategory


class AddCareTaskRequest(BaseModel):
    category: CareTaskCategory
    title: str = Field(..., min_length=1, max_length=255)
    due_date: datetime
