from app.features.dogs.application.dtos.dog_output_dto import DogOutputDTO
from app.features.dogs.application.interfaces.repositories.dog_repository import (
    DogRepositoryProtocol,
)
from app.features.dogs.application.mappers.dog_dto_mapper import DogDTOMapper
from app.features.dogs.application.queries.list_my_dogs.list_my_dogs_query import ListMyDogsQuery


class ListMyDogsQueryHandler:
    def __init__(self, dogs: DogRepositoryProtocol):
        self._dogs = dogs

    async def handle(self, query: ListMyDogsQuery) -> list[DogOutputDTO]:
        return [
            DogDTOMapper.to_output_dto(item)
            for item in await self._dogs.list_for_owner(query.actor.id)
        ]
