from collections.abc import Sequence
from typing import Protocol

from app.features.veterinarians.domain.value_objects.vet_stats import VetStats


class VetStatsProviderProtocol(Protocol):
    """Reputation figures derived from reviews and completed appointments."""

    async def stats_for(self, vet_ids: Sequence[str]) -> dict[str, VetStats]: ...
