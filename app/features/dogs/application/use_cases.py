from collections.abc import Sequence
from datetime import date
from typing import Any

from app.features.dogs.application.access import DogAccess
from app.features.dogs.domain.entities import Dog
from app.features.dogs.domain.exceptions import InvalidDogError
from app.features.dogs.domain.repositories import DogRepositoryProtocol
from app.shared.actor import Actor
from app.shared.entity import _utc_now


def _validate(dog: Dog) -> None:
    if not dog.name.strip():
        raise InvalidDogError("A Dog needs a name.")
    if dog.birth_date > date.today():
        raise InvalidDogError("Birth date cannot be in the future.")


class RegisterDogUseCase:
    def __init__(self, dogs: DogRepositoryProtocol):
        self._dogs = dogs

    async def execute(self, actor: Actor, attributes: dict[str, Any]) -> Dog:
        dog = Dog(owner_id=actor.id, **attributes)
        _validate(dog)
        return await self._dogs.create(dog)


class ListMyDogsUseCase:
    def __init__(self, dogs: DogRepositoryProtocol):
        self._dogs = dogs

    async def execute(self, actor: Actor) -> Sequence[Dog]:
        return await self._dogs.list_for_owner(actor.id)


class GetDogUseCase:
    def __init__(self, access: DogAccess):
        self._access = access

    async def execute(self, actor: Actor, dog_id: str) -> Dog:
        return await self._access.readable(actor, dog_id)


class UpdateDogUseCase:
    def __init__(self, dogs: DogRepositoryProtocol, access: DogAccess):
        self._dogs = dogs
        self._access = access

    async def execute(self, actor: Actor, dog_id: str, changes: dict[str, Any]) -> Dog:
        dog = await self._access.owned(actor, dog_id)
        for name, value in changes.items():
            setattr(dog, name, value)
        _validate(dog)
        dog.updated_at = _utc_now()
        return await self._dogs.update(dog)


class RemoveDogUseCase:
    """Archives the Dog: it disappears for its owner while its clinical history is kept."""

    def __init__(self, dogs: DogRepositoryProtocol, access: DogAccess):
        self._dogs = dogs
        self._access = access

    async def execute(self, actor: Actor, dog_id: str) -> None:
        dog = await self._access.owned(actor, dog_id)
        dog.is_archived = True
        await self._dogs.update(dog)
