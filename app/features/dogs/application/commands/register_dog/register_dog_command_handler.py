from app.features.dogs.application.commands.register_dog.register_dog_command import (
    RegisterDogCommand,
)
from app.features.dogs.application.dtos.dog_output_dto import DogOutputDTO
from app.features.dogs.application.interfaces.repositories.dog_repository import (
    DogRepositoryProtocol,
)
from app.features.dogs.application.mappers.dog_dto_mapper import DogDTOMapper
from app.features.dogs.application.services.validate_dog import validate_dog
from app.features.dogs.domain.entities.dog import Dog


class RegisterDogCommandHandler:
    def __init__(self, dogs: DogRepositoryProtocol):
        self._dogs = dogs

    async def handle(self, command: RegisterDogCommand) -> DogOutputDTO:
        dog = Dog(owner_id=command.actor.id, **command.attributes)
        validate_dog(dog)
        return DogDTOMapper.to_output_dto(await self._dogs.create(dog))
