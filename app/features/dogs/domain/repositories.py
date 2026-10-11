from collections.abc import Sequence
from typing import Protocol

from app.features.dogs.domain.entities import Dog


class DogRepositoryProtocol(Protocol):
    async def get_by_id(self, entity_id: str) -> Dog | None: ...

    async def list_for_owner(self, owner_id: int) -> Sequence[Dog]: ...

    async def list_by_ids(self, dog_ids: Sequence[str]) -> Sequence[Dog]: ...

    async def count_for_owner(self, owner_id: int) -> int: ...

    async def create(self, entity: Dog) -> Dog: ...

    async def update(self, entity: Dog) -> Dog: ...


class OwnerSharingPolicyProtocol(Protocol):
    """Whether an owner lets veterinarians see their Dogs' data (a privacy setting)."""

    async def shares_with_vets(self, owner_id: int) -> bool: ...


class PatientRegistryProtocol(Protocol):
    """Answers whether a Dog is a patient of a veterinarian (see spec: authorisation)."""

    async def is_patient(self, vet_user_id: int, dog: Dog) -> bool: ...
