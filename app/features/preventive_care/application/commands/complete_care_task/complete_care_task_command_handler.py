from app.features.preventive_care.application.commands.complete_care_task.complete_care_task_command import (
    CompleteCareTaskCommand,
)
from app.features.preventive_care.application.services.owned_task import _OwnedTask
from app.features.preventive_care.domain.entities.care_task import CareTask


class CompleteCareTaskCommandHandler(_OwnedTask):
    async def handle(self, command: CompleteCareTaskCommand) -> CareTask:
        task = await self._load(command.actor, command.dog_id, command.task_id)
        task.complete()
        return await self._tasks.update(task)
