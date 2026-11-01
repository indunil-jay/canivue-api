from dataclasses import dataclass

from app.features.nutrition.domain.value_objects.feeding_schedule_entry import FeedingScheduleEntry


@dataclass(frozen=True)
class NutritionProfile:
    current_weight_kg: float
    weight_goal_kg: float
    thirty_day_weight_change_kg: float
    body_condition_score: int
    daily_calorie_target: int
    feeding_schedule: list[FeedingScheduleEntry]
    nutrition_goal: str
