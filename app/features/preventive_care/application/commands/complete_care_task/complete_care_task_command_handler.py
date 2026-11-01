from app.features.preventive_care.application.commands.complete_care_task.complete_care_task_command import (
    CompleteCareTaskCommand,
)
from app.features.preventive_care.application.dtos.care_task_output_dto import CareTaskOutputDTO
from app.features.preventive_care.application.mappers.care_task_dto_mapper import CareTaskDTOMapper
from app.features.preventive_care.application.services.owned_task import _OwnedTask


class CompleteCareTaskCommandHandler(_OwnedTask):
    async def handle(self, command: CompleteCareTaskCommand) -> CareTaskOutputDTO:
        task = await self._load(command.actor, command.dog_id, command.task_id)
        task.complete()
        return CareTaskDTOMapper.to_output_dto(await self._tasks.update(task))
