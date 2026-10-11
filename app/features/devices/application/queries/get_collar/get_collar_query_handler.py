from app.features.devices.application.interfaces.repositories.smart_collar_repository import (
    SmartCollarRepositoryProtocol,
)
from app.features.devices.application.queries.get_collar.get_collar_query import GetCollarQuery
from app.features.devices.domain.entities.smart_collar import SmartCollar
from app.features.dogs.application.services.dog_access import DogAccess


class GetCollarQueryHandler:
    def __init__(self, collars: SmartCollarRepositoryProtocol, access: DogAccess):
        self._collars = collars
        self._access = access

    async def handle(self, query: GetCollarQuery) -> SmartCollar:
        dog = await self._access.readable(query.actor, query.dog_id)
        # A Dog with no collar on record is reported as not paired rather than as an error.
        return await self._collars.get_for_dog(dog.id) or SmartCollar(dog_id=dog.id)
