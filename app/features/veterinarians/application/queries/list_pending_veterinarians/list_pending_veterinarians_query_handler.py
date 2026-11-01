from app.features.veterinarians.application.dtos.veterinarian_view import VeterinarianView
from app.features.veterinarians.application.interfaces.repositories.vet_profile_repository import (
    VetProfileRepositoryProtocol,
)
from app.features.veterinarians.application.queries.list_pending_veterinarians.list_pending_veterinarians_query import (
    ListPendingVeterinariansQuery,
)
from app.features.veterinarians.application.services.veterinarian_views import VeterinarianViews


class ListPendingVeterinariansQueryHandler:
    def __init__(self, profiles: VetProfileRepositoryProtocol, views: VeterinarianViews):
        self._profiles = profiles
        self._views = views

    async def handle(self, query: ListPendingVeterinariansQuery) -> list[VeterinarianView]:
        return await self._views.of(await self._profiles.list_by_verified(False))
