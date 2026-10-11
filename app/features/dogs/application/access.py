from app.features.dogs.domain.entities import Dog
from app.features.dogs.domain.exceptions import DogNotFoundError
from app.features.dogs.domain.repositories import DogRepositoryProtocol, PatientRegistryProtocol
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


class AnyPatientRegistry(PatientRegistryProtocol):
    """A Dog is a patient if any of the underlying registries says so."""

    def __init__(self, *registries: PatientRegistryProtocol):
        self._registries = registries

    async def is_patient(self, vet_user_id: int, dog: Dog) -> bool:
        for registry in self._registries:
            if await registry.is_patient(vet_user_id, dog):
                return True
        return False
