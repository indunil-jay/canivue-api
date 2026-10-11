from app.features.dogs.application.commands.remove_dog.remove_dog_command import RemoveDogCommand
from app.features.dogs.application.interfaces.repositories.dog_repository import (
    DogRepositoryProtocol,
)
from app.features.dogs.application.services.dog_access import DogAccess


class RemoveDogCommandHandler:
    """Archives the Dog: it disappears for its owner while its clinical history is kept."""

    def __init__(self, dogs: DogRepositoryProtocol, access: DogAccess):
        self._dogs = dogs
        self._access = access

    async def handle(self, command: RemoveDogCommand) -> None:
        dog = await self._access.owned(command.actor, command.dog_id)
        dog.is_archived = True
        await self._dogs.update(dog)
