from dataclasses import dataclass, field

from app.features.nutrition.domain.constants import DEFAULT_GOAL, IDEAL_BODY_CONDITION
from app.features.nutrition.domain.value_objects.feeding_schedule_entry import FeedingScheduleEntry
from app.shared.entity import BaseEntity


@dataclass
class NutritionPlan(BaseEntity):
    """What the owner has chosen for a Dog. Unset values fall back to computed defaults."""

    dog_id: str = ""
    weight_goal_kg: float | None = None
    daily_calorie_target: int | None = None
    body_condition_score: int = IDEAL_BODY_CONDITION
    nutrition_goal: str = DEFAULT_GOAL
    feeding_schedule: list[FeedingScheduleEntry] = field(default_factory=list)
