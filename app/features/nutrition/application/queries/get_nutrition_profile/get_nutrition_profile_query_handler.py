from app.features.dogs.application.services.dog_access import DogAccess
from app.features.nutrition.application.queries.get_nutrition_profile.get_nutrition_profile_query import (
    GetNutritionProfileQuery,
)
from app.features.nutrition.application.services.nutrition_profiles import NutritionProfiles
from app.features.nutrition.domain.value_objects.nutrition_profile import NutritionProfile


class GetNutritionProfileQueryHandler:
    def __init__(self, profiles: NutritionProfiles, access: DogAccess):
        self._profiles = profiles
        self._access = access

    async def handle(self, query: GetNutritionProfileQuery) -> NutritionProfile:
        return await self._profiles.of(await self._access.readable(query.actor, query.dog_id))
