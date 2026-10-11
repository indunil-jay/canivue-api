from app.features.veterinarians.application.dtos.veterinarian_view import VeterinarianView
from app.features.veterinarians.application.interfaces.repositories.vet_profile_repository import (
    VetProfileRepositoryProtocol,
)
from app.features.veterinarians.application.queries.search_veterinarians.search_veterinarians_query import (
    SearchVeterinariansQuery,
)
from app.features.veterinarians.application.services.veterinarian_views import VeterinarianViews


class SearchVeterinariansQueryHandler:
    def __init__(self, profiles: VetProfileRepositoryProtocol, views: VeterinarianViews):
        self._profiles = profiles
        self._views = views

    async def handle(self, query: SearchVeterinariansQuery) -> list[VeterinarianView]:
        matching = [
            p
            for p in await self._profiles.list_by_verified(True)
            if p.matches(query.filters.query)
            and (not query.filters.specialty or p.has_specialty(query.filters.specialty))
            and (not query.filters.consultation_type or p.offers(query.filters.consultation_type))
        ]
        views = await self._views.of(matching)
        if query.filters.available_today_only:
            views = [v for v in views if v.available_today]
        return sorted(views, key=lambda v: (-v.stats.rating, v.profile.name))
