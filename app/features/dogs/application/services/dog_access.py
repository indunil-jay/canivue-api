from app.features.dogs.application.interfaces.repositories.dog_repository import (
    DogRepositoryProtocol,
)
from app.features.dogs.application.interfaces.services.patient_registry import (
    PatientRegistryProtocol,
)
from app.features.dogs.domain.entities.dog import Dog
from app.features.dogs.domain.exceptions import DogNotFoundError
from app.shared.actor import Actor


class DogAccess:
    """The single answer to "may this user reach this Dog".

    A Dog the caller may not reach is reported as not found, so its existence is not leaked.
    """

    def __init__(self, dogs: DogRepositoryProtocol, patients: PatientRegistryProtocol):
        self._dogs = dogs
        self._patients = patients

    async def _load(self, dog_id: str) -> Dog:
        dog = await self._dogs.get_by_id(dog_id)
        if dog is None or dog.is_archived:
            raise DogNotFoundError()
        return dog

    async def _is_treating_vet(self, actor: Actor, dog: Dog) -> bool:
        return actor.is_vet and await self._patients.is_patient(actor.id, dog)

    async def readable(self, actor: Actor, dog_id: str) -> Dog:
        dog = await self._load(dog_id)
        if actor.is_admin or dog.owner_id == actor.id or await self._is_treating_vet(actor, dog):
            return dog
        raise DogNotFoundError()

    async def owned(self, actor: Actor, dog_id: str) -> Dog:
        dog = await self._load(dog_id)
        if actor.is_admin or dog.owner_id == actor.id:
            return dog
        raise DogNotFoundError()

    async def treatable(self, actor: Actor, dog_id: str) -> Dog:
        dog = await self._load(dog_id)
        if actor.is_admin or await self._is_treating_vet(actor, dog):
            return dog
        raise DogNotFoundError()
