from app.features.veterinarians.application.dtos.veterinarian_view import VeterinarianView
from app.features.veterinarians.application.queries.get_my_vet_profile.get_my_vet_profile_query import (
    GetMyVetProfileQuery,
)
from app.features.veterinarians.application.services.veterinarian_onboarding import (
    VeterinarianOnboarding,
)
from app.features.veterinarians.application.services.veterinarian_views import VeterinarianViews


class GetMyVetProfileQueryHandler:
    def __init__(self, onboarding: VeterinarianOnboarding, views: VeterinarianViews):
        self._onboarding = onboarding
        self._views = views

    async def handle(self, query: GetMyVetProfileQuery) -> VeterinarianView:
        return await self._views.one(
            await self._onboarding.ensure_profile(query.actor.id, query.actor.name)
        )
