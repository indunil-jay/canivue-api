from app.features.devices.application.interfaces.repositories.smart_collar_repository import (
    SmartCollarRepositoryProtocol,
)
from app.features.devices.domain.entities.smart_collar import SmartCollar
from app.features.dogs.application.services.dog_access import DogAccess
from app.shared.actor import Actor


class _OwnedCollar:
    def __init__(self, collars: SmartCollarRepositoryProtocol, access: DogAccess):
        self._collars = collars
        self._access = access

    async def _load(self, actor: Actor, dog_id: str) -> SmartCollar:
        dog = await self._access.owned(actor, dog_id)
        return await self._collars.get_for_dog(dog.id) or SmartCollar(dog_id=dog.id)
