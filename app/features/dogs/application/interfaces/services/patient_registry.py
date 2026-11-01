from typing import Protocol

from app.features.dogs.domain.entities.dog import Dog


class PatientRegistryProtocol(Protocol):
    """Answers whether a Dog is a patient of a veterinarian (see spec: authorisation)."""

    async def is_patient(self, vet_user_id: int, dog: Dog) -> bool: ...
