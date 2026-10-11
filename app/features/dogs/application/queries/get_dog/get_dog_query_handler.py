from app.features.dogs.application.dtos.dog_output_dto import DogOutputDTO
from app.features.dogs.application.mappers.dog_dto_mapper import DogDTOMapper
from app.features.dogs.application.queries.get_dog.get_dog_query import GetDogQuery
from app.features.dogs.application.services.dog_access import DogAccess


class GetDogQueryHandler:
    def __init__(self, access: DogAccess):
        self._access = access

    async def handle(self, query: GetDogQuery) -> DogOutputDTO:
        return DogDTOMapper.to_output_dto(await self._access.readable(query.actor, query.dog_id))
