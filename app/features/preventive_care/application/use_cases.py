from collections.abc import Sequence
from datetime import datetime, timezone

from app.features.dogs.application.access import DogAccess
from app.features.preventive_care.domain.entities import (
    CareTask,
    CareTaskCategory,
    CareTaskNotFoundError,
    CareTaskRepositoryProtocol,
)
from app.shared.actor import Actor


class ListCareTasksUseCase:
    def __init__(self, tasks: CareTaskRepositoryProtocol, access: DogAccess):
        self._tasks = tasks
        self._access = access

    async def execute(self, actor: Actor, dog_id: str) -> Sequence[CareTask]:
        dog = await self._access.readable(actor, dog_id)
        return await self._tasks.list_for_dog(dog.id)


class AddCareTaskUseCase:
    def __init__(self, tasks: CareTaskRepositoryProtocol, access: DogAccess):
        self._tasks = tasks
        self._access = access

    async def execute(
        self, actor: Actor, dog_id: str, category: CareTaskCategory, title: str, due_date: datetime
    ) -> CareTask:
        dog = await self._access.owned(actor, dog_id)
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)
        return await self._tasks.create(
            CareTask(dog_id=dog.id, category=category, title=title.strip(), due_date=due_date)
        )


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


class CompleteCareTaskUseCase(_OwnedTask):
    async def execute(self, actor: Actor, dog_id: str, task_id: str) -> CareTask:
        task = await self._load(actor, dog_id, task_id)
        task.complete()
        return await self._tasks.update(task)


class RemoveCareTaskUseCase(_OwnedTask):
    async def execute(self, actor: Actor, dog_id: str, task_id: str) -> None:
        task = await self._load(actor, dog_id, task_id)
        await self._tasks.delete(task.id)
