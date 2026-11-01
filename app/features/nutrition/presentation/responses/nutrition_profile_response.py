from pydantic import BaseModel, ConfigDict, Field

from app.features.nutrition.presentation.schemas.feeding_schedule_entry_schema import (
    FeedingScheduleEntrySchema,
)


class NutritionProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    current_weight_kg: float
    weight_goal_kg: float
    thirty_day_weight_change_kg: float
    body_condition_score: int = Field(..., description="1-9; 4-5 is ideal")
    daily_calorie_target: int
    feeding_schedule: list[FeedingScheduleEntrySchema]
    nutrition_goal: str
