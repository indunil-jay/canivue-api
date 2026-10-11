from app.features.devices.domain.entities import SmartCollar, SmartCollarRepositoryProtocol
from app.features.dogs.application.access import DogAccess
from app.shared.actor import Actor


class GetCollarUseCase:
    def __init__(self, collars: SmartCollarRepositoryProtocol, access: DogAccess):
        self._collars = collars
        self._access = access

    async def execute(self, actor: Actor, dog_id: str) -> SmartCollar:
        dog = await self._access.readable(actor, dog_id)
        # A Dog with no collar on record is reported as not paired rather than as an error.
        return await self._collars.get_for_dog(dog.id) or SmartCollar(dog_id=dog.id)


class _OwnedCollar:
    def __init__(self, collars: SmartCollarRepositoryProtocol, access: DogAccess):
        self._collars = collars
        self._access = access

    async def _load(self, actor: Actor, dog_id: str) -> SmartCollar:
        dog = await self._access.owned(actor, dog_id)
        return await self._collars.get_for_dog(dog.id) or SmartCollar(dog_id=dog.id)


class PairCollarUseCase(_OwnedCollar):
    async def execute(self, actor: Actor, dog_id: str) -> SmartCollar:
        collar = await self._load(actor, dog_id)
        collar.pair()
        return await self._collars.save(collar)


class DisconnectCollarUseCase(_OwnedCollar):
    async def execute(self, actor: Actor, dog_id: str) -> SmartCollar:
        collar = await self._load(actor, dog_id)
        collar.disconnect()
        return await self._collars.save(collar)


class RenameCollarUseCase(_OwnedCollar):
    async def execute(self, actor: Actor, dog_id: str, name: str) -> SmartCollar:
        collar = await self._load(actor, dog_id)
        collar.rename(name)
        return await self._collars.save(collar)


class SyncCollarUseCase(_OwnedCollar):
    async def execute(
        self, actor: Actor, dog_id: str, records_synced: int, battery_percent: int | None
    ) -> SmartCollar:
        collar = await self._load(actor, dog_id)
        collar.record_sync(records_synced, battery_percent)
        return await self._collars.save(collar)
