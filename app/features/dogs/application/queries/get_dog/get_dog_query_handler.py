from app.features.dogs.application.queries.get_dog.get_dog_query import GetDogQuery
from app.features.dogs.application.services.dog_access import DogAccess
from app.features.dogs.domain.entities.dog import Dog


class GetDogQueryHandler:
    def __init__(self, access: DogAccess):
        self._access = access

    async def handle(self, query: GetDogQuery) -> Dog:
        return await self._access.readable(query.actor, query.dog_id)
