from typing import Protocol

from app.features.devices.domain.entities.smart_collar import SmartCollar


class SmartCollarRepositoryProtocol(Protocol):
    async def get_for_dog(self, dog_id: str) -> SmartCollar | None: ...

    async def save(self, collar: SmartCollar) -> SmartCollar: ...
