from dataclasses import dataclass, field
from typing import Protocol

from app.shared.entity import BaseEntity

DEFAULT_GOAL = "Maintain a healthy weight"
IDEAL_BODY_CONDITION = 5


@dataclass(frozen=True)
class FeedingScheduleEntry:
    time: str
    food_name: str
    portion_grams: int


@dataclass
class NutritionPlan(BaseEntity):
    """What the owner has chosen for a Dog. Unset values fall back to computed defaults."""

    dog_id: str = ""
    weight_goal_kg: float | None = None
    daily_calorie_target: int | None = None
    body_condition_score: int = IDEAL_BODY_CONDITION
    nutrition_goal: str = DEFAULT_GOAL
    feeding_schedule: list[FeedingScheduleEntry] = field(default_factory=list)


@dataclass(frozen=True)
class NutritionProfile:
    current_weight_kg: float
    weight_goal_kg: float
    thirty_day_weight_change_kg: float
    body_condition_score: int
    daily_calorie_target: int
    feeding_schedule: list[FeedingScheduleEntry]
    nutrition_goal: str


def maintenance_calories(weight_kg: float) -> int:
    """Resting energy requirement (70 x kg^0.75) times 1.6 for a typical neutered adult."""
    return round(70 * weight_kg**0.75 * 1.6) if weight_kg > 0 else 0


class NutritionPlanRepositoryProtocol(Protocol):
    async def get_for_dog(self, dog_id: str) -> NutritionPlan | None: ...

    async def save(self, plan: NutritionPlan) -> NutritionPlan: ...
