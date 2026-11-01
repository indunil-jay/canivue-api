from datetime import timezone

from app.features.dogs.application.services.dog_access import DogAccess
from app.features.preventive_care.application.commands.add_care_task.add_care_task_command import (
    AddCareTaskCommand,
)
from app.features.preventive_care.application.dtos.care_task_output_dto import CareTaskOutputDTO
from app.features.preventive_care.application.interfaces.repositories.care_task_repository import (
    CareTaskRepositoryProtocol,
)
from app.features.preventive_care.application.mappers.care_task_dto_mapper import CareTaskDTOMapper
from app.features.preventive_care.domain.entities.care_task import CareTask


class AddCareTaskCommandHandler:
    def __init__(self, tasks: CareTaskRepositoryProtocol, access: DogAccess):
        self._tasks = tasks
        self._access = access

    async def handle(self, command: AddCareTaskCommand) -> CareTaskOutputDTO:
        due_date = command.due_date
        dog = await self._access.owned(command.actor, command.dog_id)
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)
        return CareTaskDTOMapper.to_output_dto(
            await self._tasks.create(
                CareTask(
                    dog_id=dog.id,
                    category=command.category,
                    title=command.title.strip(),
                    due_date=due_date,
                )
            )
        )
