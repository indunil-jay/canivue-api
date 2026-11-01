from collections.abc import Sequence
from typing import Protocol

from app.features.reviews.domain.entities.review import Review


class ReviewRepositoryProtocol(Protocol):
    async def create(self, entity: Review) -> Review: ...

    async def exists_for_appointment(self, appointment_id: str) -> bool: ...

    async def list_for_vet(self, vet_id: str) -> Sequence[Review]: ...
