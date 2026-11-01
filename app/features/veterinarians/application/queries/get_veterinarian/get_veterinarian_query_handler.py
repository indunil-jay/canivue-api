from app.features.veterinarians.application.dtos.veterinarian_view import VeterinarianView
from app.features.veterinarians.application.interfaces.repositories.vet_profile_repository import (
    VetProfileRepositoryProtocol,
)
from app.features.veterinarians.application.queries.get_veterinarian.get_veterinarian_query import (
    GetVeterinarianQuery,
)
from app.features.veterinarians.application.services.veterinarian_views import VeterinarianViews
from app.features.veterinarians.domain.exceptions import VeterinarianNotFoundError


class GetVeterinarianQueryHandler:
    def __init__(self, profiles: VetProfileRepositoryProtocol, views: VeterinarianViews):
        self._profiles = profiles
        self._views = views

    async def handle(self, query: GetVeterinarianQuery) -> VeterinarianView:
        profile = await self._profiles.get_by_id(query.vet_id)
        # Unverified veterinarians are visible only to themselves and administrators.
        if profile is None or not (
            profile.verified or query.actor.is_admin or profile.user_id == query.actor.id
        ):
            raise VeterinarianNotFoundError()
        return await self._views.one(profile)
