from collections.abc import Sequence
from datetime import datetime, timezone

from app.features.veterinarians.application.dtos.veterinarian_view import VeterinarianView
from app.features.veterinarians.application.interfaces.services.vet_stats_provider import (
    VetStatsProviderProtocol,
)
from app.features.veterinarians.application.mappers.vet_profile_dto_mapper import (
    VetProfileDTOMapper,
)
from app.features.veterinarians.domain.entities.vet_profile import VetProfile
from app.features.veterinarians.domain.value_objects.vet_stats import VetStats


class VeterinarianViews:
    def __init__(self, stats: VetStatsProviderProtocol):
        self._stats = stats

    async def of(self, profiles: Sequence[VetProfile]) -> list[VeterinarianView]:
        stats = await self._stats.stats_for([p.id for p in profiles])
        now = datetime.now(timezone.utc)
        return [
            VeterinarianView(
                VetProfileDTOMapper.to_output_dto(p),
                stats.get(p.id, VetStats()),
                p.is_available_on(now),
            )
            for p in profiles
        ]

    async def one(self, profile: VetProfile) -> VeterinarianView:
        return (await self.of([profile]))[0]
