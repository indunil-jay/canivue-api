from app.features.devices.application.commands.disconnect_collar.disconnect_collar_command import (
    DisconnectCollarCommand,
)
from app.features.devices.application.dtos.smart_collar_output_dto import SmartCollarOutputDTO
from app.features.devices.application.mappers.smart_collar_dto_mapper import SmartCollarDTOMapper
from app.features.devices.application.services.owned_collar import _OwnedCollar


class DisconnectCollarCommandHandler(_OwnedCollar):
    async def handle(self, command: DisconnectCollarCommand) -> SmartCollarOutputDTO:
        collar = await self._load(command.actor, command.dog_id)
        collar.disconnect()
        return SmartCollarDTOMapper.to_output_dto(await self._collars.save(collar))
