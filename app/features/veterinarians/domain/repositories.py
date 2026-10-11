from collections.abc import Sequence
from typing import Protocol

from app.features.veterinarians.domain.entities import VetProfile, VetStats


class VetProfileRepositoryProtocol(Protocol):
    async def get_by_id(self, entity_id: str) -> VetProfile | None: ...

    async def get_by_user_id(self, user_id: int) -> VetProfile | None: ...

    async def list_by_verified(self, verified: bool) -> Sequence[VetProfile]: ...

    async def create(self, entity: VetProfile) -> VetProfile: ...

    async def update(self, entity: VetProfile) -> VetProfile: ...


class VetStatsProviderProtocol(Protocol):
    """Reputation figures derived from reviews and completed appointments."""

    async def stats_for(self, vet_ids: Sequence[str]) -> dict[str, VetStats]: ...
