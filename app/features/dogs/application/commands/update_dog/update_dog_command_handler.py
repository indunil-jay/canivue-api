from app.features.dogs.application.commands.update_dog.update_dog_command import UpdateDogCommand
from app.features.dogs.application.dtos.dog_output_dto import DogOutputDTO
from app.features.dogs.application.interfaces.repositories.dog_repository import (
    DogRepositoryProtocol,
)
from app.features.dogs.application.mappers.dog_dto_mapper import DogDTOMapper
from app.features.dogs.application.services.dog_access import DogAccess
from app.features.dogs.application.services.validate_dog import validate_dog
from app.shared.entity import _utc_now


class UpdateDogCommandHandler:
    def __init__(self, dogs: DogRepositoryProtocol, access: DogAccess):
        self._dogs = dogs
        self._access = access

    async def handle(self, command: UpdateDogCommand) -> DogOutputDTO:
        dog = await self._access.owned(command.actor, command.dog_id)
        for name, value in command.changes.items():
            setattr(dog, name, value)
        validate_dog(dog)
        dog.updated_at = _utc_now()
        return DogDTOMapper.to_output_dto(await self._dogs.update(dog))
