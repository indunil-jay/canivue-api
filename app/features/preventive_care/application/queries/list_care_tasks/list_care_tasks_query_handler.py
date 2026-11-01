from app.features.dogs.application.services.dog_access import DogAccess
from app.features.preventive_care.application.dtos.care_task_output_dto import CareTaskOutputDTO
from app.features.preventive_care.application.interfaces.repositories.care_task_repository import (
    CareTaskRepositoryProtocol,
)
from app.features.preventive_care.application.mappers.care_task_dto_mapper import CareTaskDTOMapper
from app.features.preventive_care.application.queries.list_care_tasks.list_care_tasks_query import (
    ListCareTasksQuery,
)


class ListCareTasksQueryHandler:
    def __init__(self, tasks: CareTaskRepositoryProtocol, access: DogAccess):
        self._tasks = tasks
        self._access = access

    async def handle(self, query: ListCareTasksQuery) -> list[CareTaskOutputDTO]:
        dog = await self._access.readable(query.actor, query.dog_id)
        return [
            CareTaskDTOMapper.to_output_dto(item) for item in await self._tasks.list_for_dog(dog.id)
        ]
