from datetime import datetime, timedelta, timezone

from app.features.dogs.domain.entities.dog import Dog
from app.features.health_metrics.application.interfaces.repositories.metric_reading_repository import (
    MetricReadingRepositoryProtocol,
)
from app.features.health_metrics.domain.enums.health_metric import HealthMetric
from app.features.nutrition.application.interfaces.repositories.nutrition_plan_repository import (
    NutritionPlanRepositoryProtocol,
)
from app.features.nutrition.domain.entities.nutrition_plan import NutritionPlan
from app.features.nutrition.domain.services.maintenance_calories import maintenance_calories
from app.features.nutrition.domain.value_objects.nutrition_profile import NutritionProfile


class NutritionProfiles:
    def __init__(
        self, plans: NutritionPlanRepositoryProtocol, readings: MetricReadingRepositoryProtocol
    ):
        self._plans = plans
        self._readings = readings

    async def of(self, dog: Dog, plan: NutritionPlan | None = None) -> NutritionProfile:
        plan = plan or await self._plans.get_for_dog(dog.id) or NutritionPlan(dog_id=dog.id)
        since = datetime.now(timezone.utc) - timedelta(days=30)
        weights = await self._readings.list_since(dog.id, HealthMetric.WEIGHT, since)
        latest = await self._readings.latest(dog.id, HealthMetric.WEIGHT)
        # Weight readings win over the weight typed into the Dog's profile.
        current = latest.value if latest else dog.weight_kg
        change = weights[-1].value - weights[0].value if len(weights) > 1 else 0.0
        return NutritionProfile(
            current_weight_kg=round(current, 2),
            weight_goal_kg=plan.weight_goal_kg or round(current, 2),
            thirty_day_weight_change_kg=round(change, 2),
            body_condition_score=plan.body_condition_score,
            daily_calorie_target=plan.daily_calorie_target
            or maintenance_calories(plan.weight_goal_kg or current),
            feeding_schedule=plan.feeding_schedule,
            nutrition_goal=plan.nutrition_goal,
        )
