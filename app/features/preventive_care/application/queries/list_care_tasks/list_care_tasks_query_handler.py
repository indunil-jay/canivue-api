from collections.abc import Sequence

from app.features.dogs.application.services.dog_access import DogAccess
from app.features.preventive_care.application.interfaces.repositories.care_task_repository import (
    CareTaskRepositoryProtocol,
)
from app.features.preventive_care.application.queries.list_care_tasks.list_care_tasks_query import (
    ListCareTasksQuery,
)
from app.features.preventive_care.domain.entities.care_task import CareTask


class ListCareTasksQueryHandler:
    def __init__(self, tasks: CareTaskRepositoryProtocol, access: DogAccess):
        self._tasks = tasks
        self._access = access

    async def handle(self, query: ListCareTasksQuery) -> Sequence[CareTask]:
        dog = await self._access.readable(query.actor, query.dog_id)
        return await self._tasks.list_for_dog(dog.id)
