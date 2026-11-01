from app.features.dogs.application.commands.set_dog_photo.set_dog_photo_command import (
    SetDogPhotoCommand,
)
from app.features.dogs.application.dtos.dog_output_dto import DogOutputDTO
from app.features.dogs.application.interfaces.repositories.dog_repository import (
    DogRepositoryProtocol,
)
from app.features.dogs.application.mappers.dog_dto_mapper import DogDTOMapper
from app.features.dogs.application.services.dog_access import DogAccess
from app.shared.files import (
    IMAGE_TYPES,
    FileStorageProtocol,
    validate_upload,
)


class SetDogPhotoCommandHandler:
    def __init__(
        self, dogs: DogRepositoryProtocol, access: DogAccess, storage: FileStorageProtocol
    ):
        self._dogs = dogs
        self._access = access
        self._storage = storage

    async def handle(self, command: SetDogPhotoCommand) -> DogOutputDTO:
        dog = await self._access.owned(command.actor, command.dog_id)
        accepted_type = validate_upload(
            command.content, command.content_type, IMAGE_TYPES, command.max_bytes
        )
        previous = dog.photo_file_id
        dog.photo_file_id = await self._storage.save(command.content, accepted_type)
        dog = await self._dogs.update(dog)
        if previous:
            await self._storage.delete(previous)
        return DogDTOMapper.to_output_dto(dog)
