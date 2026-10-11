from app.features.devices.application.commands.rename_collar.rename_collar_command import (
    RenameCollarCommand,
)
from app.features.devices.application.services.owned_collar import _OwnedCollar
from app.features.devices.domain.entities.smart_collar import SmartCollar


class RenameCollarCommandHandler(_OwnedCollar):
    async def handle(self, command: RenameCollarCommand) -> SmartCollar:
        collar = await self._load(command.actor, command.dog_id)
        collar.rename(command.name)
        return await self._collars.save(collar)
