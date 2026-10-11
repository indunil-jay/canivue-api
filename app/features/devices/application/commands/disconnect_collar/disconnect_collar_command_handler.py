from app.features.devices.application.commands.disconnect_collar.disconnect_collar_command import (
    DisconnectCollarCommand,
)
from app.features.devices.application.services.owned_collar import _OwnedCollar
from app.features.devices.domain.entities.smart_collar import SmartCollar


class DisconnectCollarCommandHandler(_OwnedCollar):
    async def handle(self, command: DisconnectCollarCommand) -> SmartCollar:
        collar = await self._load(command.actor, command.dog_id)
        collar.disconnect()
        return await self._collars.save(collar)
