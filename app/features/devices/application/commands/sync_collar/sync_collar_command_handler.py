from app.features.devices.application.commands.sync_collar.sync_collar_command import (
    SyncCollarCommand,
)
from app.features.devices.application.services.owned_collar import _OwnedCollar
from app.features.devices.domain.entities.smart_collar import SmartCollar


class SyncCollarCommandHandler(_OwnedCollar):
    async def handle(self, command: SyncCollarCommand) -> SmartCollar:
        collar = await self._load(command.actor, command.dog_id)
        collar.record_sync(command.records_synced, command.battery_percent)
        return await self._collars.save(collar)
