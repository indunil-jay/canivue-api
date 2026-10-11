from app.features.dogs.application.commands.update_dog.update_dog_command import UpdateDogCommand
from app.features.dogs.application.interfaces.repositories.dog_repository import (
    DogRepositoryProtocol,
)
from app.features.dogs.application.services.dog_access import DogAccess
from app.features.dogs.application.services.validate_dog import validate_dog
from app.features.dogs.domain.entities.dog import Dog
from app.shared.entity import _utc_now


class UpdateDogCommandHandler:
    def __init__(self, dogs: DogRepositoryProtocol, access: DogAccess):
        self._dogs = dogs
        self._access = access

    async def handle(self, command: UpdateDogCommand) -> Dog:
        dog = await self._access.owned(command.actor, command.dog_id)
        for name, value in command.changes.items():
            setattr(dog, name, value)
        validate_dog(dog)
        dog.updated_at = _utc_now()
        return await self._dogs.update(dog)
