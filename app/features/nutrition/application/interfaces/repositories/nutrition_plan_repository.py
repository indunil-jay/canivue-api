from typing import Protocol

from app.features.nutrition.domain.entities.nutrition_plan import NutritionPlan


class NutritionPlanRepositoryProtocol(Protocol):
    async def get_for_dog(self, dog_id: str) -> NutritionPlan | None: ...

    async def save(self, plan: NutritionPlan) -> NutritionPlan: ...
