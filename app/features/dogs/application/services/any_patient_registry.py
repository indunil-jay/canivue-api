from app.features.dogs.application.interfaces.services.patient_registry import (
    PatientRegistryProtocol,
)
from app.features.dogs.domain.entities.dog import Dog


class AnyPatientRegistry(PatientRegistryProtocol):
    """A Dog is a patient if any of the underlying registries says so."""

    def __init__(self, *registries: PatientRegistryProtocol):
        self._registries = registries

    async def is_patient(self, vet_user_id: int, dog: Dog) -> bool:
        for registry in self._registries:
            if await registry.is_patient(vet_user_id, dog):
                return True
        return False
