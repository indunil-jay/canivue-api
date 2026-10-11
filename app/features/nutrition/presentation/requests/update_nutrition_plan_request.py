from typing import Any

from pydantic import BaseModel, Field

from app.features.nutrition.domain.value_objects.feeding_schedule_entry import FeedingScheduleEntry
from app.features.nutrition.presentation.schemas.feeding_schedule_entry_schema import (
    FeedingScheduleEntrySchema,
)


class UpdateNutritionPlanRequest(BaseModel):
    weight_goal_kg: float | None = Field(None, gt=0, le=150)
    daily_calorie_target: int | None = Field(None, gt=0, le=10_000)
    body_condition_score: int | None = Field(None, ge=1, le=9)
    nutrition_goal: str | None = Field(None, min_length=1, max_length=255)
    feeding_schedule: list[FeedingScheduleEntrySchema] | None = None

    def to_domain(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            name: getattr(self, name)
            for name in self.model_fields_set
            if getattr(self, name) is not None
        }
        if "feeding_schedule" in data:
            data["feeding_schedule"] = sorted(
                (FeedingScheduleEntry(**e.model_dump()) for e in data["feeding_schedule"]),
                key=lambda e: e.time,
            )
        return data
