from app.features.dogs.application.services.dog_access import DogAccess
from app.features.nutrition.application.commands.update_nutrition_plan.update_nutrition_plan_command import (
    UpdateNutritionPlanCommand,
)
from app.features.nutrition.application.interfaces.repositories.nutrition_plan_repository import (
    NutritionPlanRepositoryProtocol,
)
from app.features.nutrition.application.services.nutrition_profiles import NutritionProfiles
from app.features.nutrition.domain.entities.nutrition_plan import NutritionPlan
from app.features.nutrition.domain.value_objects.nutrition_profile import NutritionProfile
from app.shared.entity import _utc_now


class UpdateNutritionPlanCommandHandler:
    def __init__(
        self,
        plans: NutritionPlanRepositoryProtocol,
        profiles: NutritionProfiles,
        access: DogAccess,
    ):
        self._plans = plans
        self._profiles = profiles
        self._access = access

    async def handle(self, command: UpdateNutritionPlanCommand) -> NutritionProfile:
        dog = await self._access.owned(command.actor, command.dog_id)
        plan = await self._plans.get_for_dog(dog.id) or NutritionPlan(dog_id=dog.id)
        for name, value in command.changes.items():
            setattr(plan, name, value)
        plan.updated_at = _utc_now()
        return await self._profiles.of(dog, await self._plans.save(plan))
