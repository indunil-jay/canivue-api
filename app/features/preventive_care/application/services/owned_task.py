from app.features.dogs.application.services.dog_access import DogAccess
from app.features.preventive_care.application.interfaces.repositories.care_task_repository import (
    CareTaskRepositoryProtocol,
)
from app.features.preventive_care.domain.entities.care_task import CareTask
from app.features.preventive_care.domain.exceptions import CareTaskNotFoundError
from app.shared.actor import Actor


class _OwnedTask:
    def __init__(self, tasks: CareTaskRepositoryProtocol, access: DogAccess):
        self._tasks = tasks
        self._access = access

    async def _load(self, actor: Actor, dog_id: str, task_id: str) -> CareTask:
        dog = await self._access.owned(actor, dog_id)
        task = await self._tasks.get_by_id(task_id)
        if task is None or task.dog_id != dog.id:
            raise CareTaskNotFoundError()
        return task
