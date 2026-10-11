from app.features.devices.application.commands.sync_collar.sync_collar_command import (
    SyncCollarCommand,
)
from app.features.devices.application.dtos.smart_collar_output_dto import SmartCollarOutputDTO
from app.features.devices.application.mappers.smart_collar_dto_mapper import SmartCollarDTOMapper
from app.features.devices.application.services.owned_collar import _OwnedCollar


class SyncCollarCommandHandler(_OwnedCollar):
    async def handle(self, command: SyncCollarCommand) -> SmartCollarOutputDTO:
        collar = await self._load(command.actor, command.dog_id)
        collar.record_sync(command.records_synced, command.battery_percent)
        return SmartCollarDTOMapper.to_output_dto(await self._collars.save(collar))
