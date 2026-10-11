from app.features.dogs.application.commands.remove_dog_photo.remove_dog_photo_command import (
    RemoveDogPhotoCommand,
)
from app.features.dogs.application.interfaces.repositories.dog_repository import (
    DogRepositoryProtocol,
)
from app.features.dogs.application.services.dog_access import DogAccess
from app.features.dogs.domain.entities.dog import Dog
from app.shared.files import (
    FileStorageProtocol,
)


class RemoveDogPhotoCommandHandler:
    def __init__(
        self, dogs: DogRepositoryProtocol, access: DogAccess, storage: FileStorageProtocol
    ):
        self._dogs = dogs
        self._access = access
        self._storage = storage

    async def handle(self, command: RemoveDogPhotoCommand) -> Dog:
        dog = await self._access.owned(command.actor, command.dog_id)
        if dog.photo_file_id:
            await self._storage.delete(dog.photo_file_id)
            dog.photo_file_id = None
            dog = await self._dogs.update(dog)
        return dog
