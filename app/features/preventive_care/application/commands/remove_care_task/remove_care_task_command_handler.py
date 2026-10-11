from app.features.preventive_care.application.commands.remove_care_task.remove_care_task_command import (
    RemoveCareTaskCommand,
)
from app.features.preventive_care.application.services.owned_task import _OwnedTask


class RemoveCareTaskCommandHandler(_OwnedTask):
    async def handle(self, command: RemoveCareTaskCommand) -> None:
        task = await self._load(command.actor, command.dog_id, command.task_id)
        await self._tasks.delete(task.id)
