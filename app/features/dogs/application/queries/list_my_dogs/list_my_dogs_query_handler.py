from collections.abc import Sequence

from app.features.dogs.application.interfaces.repositories.dog_repository import (
    DogRepositoryProtocol,
)
from app.features.dogs.application.queries.list_my_dogs.list_my_dogs_query import ListMyDogsQuery
from app.features.dogs.domain.entities.dog import Dog


class ListMyDogsQueryHandler:
    def __init__(self, dogs: DogRepositoryProtocol):
        self._dogs = dogs

    async def handle(self, query: ListMyDogsQuery) -> Sequence[Dog]:
        return await self._dogs.list_for_owner(query.actor.id)
