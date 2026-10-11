from app.features.devices.application.commands.pair_collar.pair_collar_command import (
    PairCollarCommand,
)
from app.features.devices.application.services.owned_collar import _OwnedCollar
from app.features.devices.domain.entities.smart_collar import SmartCollar


class PairCollarCommandHandler(_OwnedCollar):
    async def handle(self, command: PairCollarCommand) -> SmartCollar:
        collar = await self._load(command.actor, command.dog_id)
        collar.pair()
        return await self._collars.save(collar)
