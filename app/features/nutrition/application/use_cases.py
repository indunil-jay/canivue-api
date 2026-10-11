from datetime import datetime, timedelta, timezone
from typing import Any

from app.features.dogs.application.access import DogAccess
from app.features.dogs.domain.entities import Dog
from app.features.health_metrics.domain.entities import (
    HealthMetric,
    MetricReadingRepositoryProtocol,
)
from app.features.nutrition.domain.entities import (
    NutritionPlan,
    NutritionPlanRepositoryProtocol,
    NutritionProfile,
    maintenance_calories,
)
from app.shared.actor import Actor
from app.shared.entity import _utc_now


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


class GetNutritionProfileUseCase:
    def __init__(self, profiles: NutritionProfiles, access: DogAccess):
        self._profiles = profiles
        self._access = access

    async def execute(self, actor: Actor, dog_id: str) -> NutritionProfile:
        return await self._profiles.of(await self._access.readable(actor, dog_id))


class UpdateNutritionPlanUseCase:
    def __init__(
        self,
        plans: NutritionPlanRepositoryProtocol,
        profiles: NutritionProfiles,
        access: DogAccess,
    ):
        self._plans = plans
        self._profiles = profiles
        self._access = access

    async def execute(self, actor: Actor, dog_id: str, changes: dict[str, Any]) -> NutritionProfile:
        dog = await self._access.owned(actor, dog_id)
        plan = await self._plans.get_for_dog(dog.id) or NutritionPlan(dog_id=dog.id)
        for name, value in changes.items():
            setattr(plan, name, value)
        plan.updated_at = _utc_now()
        return await self._profiles.of(dog, await self._plans.save(plan))
