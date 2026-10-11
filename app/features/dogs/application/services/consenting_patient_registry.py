from app.features.dogs.application.interfaces.services.owner_sharing_policy import (
    OwnerSharingPolicyProtocol,
)
from app.features.dogs.application.interfaces.services.patient_registry import (
    PatientRegistryProtocol,
)
from app.features.dogs.domain.entities.dog import Dog


class ConsentingPatientRegistry(PatientRegistryProtocol):
    """Applies the owner's "share with vet" privacy setting on top of another registry."""

    def __init__(self, inner: PatientRegistryProtocol, sharing: OwnerSharingPolicyProtocol):
        self._inner = inner
        self._sharing = sharing

    async def is_patient(self, vet_user_id: int, dog: Dog) -> bool:
        return await self._inner.is_patient(vet_user_id, dog) and (
            await self._sharing.shares_with_vets(dog.owner_id)
        )
