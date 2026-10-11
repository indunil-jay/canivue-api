from app.features.veterinarians.application.queries.get_my_availability.get_my_availability_query import (
    GetMyAvailabilityQuery,
)
from app.features.veterinarians.application.services.veterinarian_onboarding import (
    VeterinarianOnboarding,
)
from app.features.veterinarians.domain.constants import WEEKDAYS


class GetMyAvailabilityQueryHandler:
    def __init__(self, onboarding: VeterinarianOnboarding):
        self._onboarding = onboarding

    async def handle(self, query: GetMyAvailabilityQuery) -> dict[str, bool]:
        profile = await self._onboarding.ensure_profile(query.actor.id, query.actor.name)
        return {day: profile.availability.get(day, False) for day in WEEKDAYS}
