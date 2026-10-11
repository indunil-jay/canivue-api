from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.features.dogs.application.services.dog_access import DogAccess
from app.features.dogs.presentation.dependencies import get_dog_access
from app.features.preventive_care.application.commands.add_care_task.add_care_task_command_handler import (
    AddCareTaskCommandHandler,
)
from app.features.preventive_care.application.commands.complete_care_task.complete_care_task_command_handler import (
    CompleteCareTaskCommandHandler,
)
from app.features.preventive_care.application.commands.remove_care_task.remove_care_task_command_handler import (
    RemoveCareTaskCommandHandler,
)
from app.features.preventive_care.application.interfaces.repositories.care_task_repository import (
    CareTaskRepositoryProtocol,
)
from app.features.preventive_care.application.queries.list_care_tasks.list_care_tasks_query_handler import (
    ListCareTasksQueryHandler,
)
from app.features.preventive_care.infrastructure.persistence.repositories.care_task_repository import (
    SqlAlchemyCareTaskRepository,
)


def get_care_task_repository(
    session: AsyncSession = Depends(get_db_session),
) -> CareTaskRepositoryProtocol:
    return SqlAlchemyCareTaskRepository(session=session)


def get_list_care_tasks_query_handler(
    tasks: CareTaskRepositoryProtocol = Depends(get_care_task_repository),
    access: DogAccess = Depends(get_dog_access),
) -> ListCareTasksQueryHandler:
    return ListCareTasksQueryHandler(tasks, access)


def get_add_care_task_command_handler(
    tasks: CareTaskRepositoryProtocol = Depends(get_care_task_repository),
    access: DogAccess = Depends(get_dog_access),
) -> AddCareTaskCommandHandler:
    return AddCareTaskCommandHandler(tasks, access)


def get_complete_care_task_command_handler(
    tasks: CareTaskRepositoryProtocol = Depends(get_care_task_repository),
    access: DogAccess = Depends(get_dog_access),
) -> CompleteCareTaskCommandHandler:
    return CompleteCareTaskCommandHandler(tasks, access)


def get_remove_care_task_command_handler(
    tasks: CareTaskRepositoryProtocol = Depends(get_care_task_repository),
    access: DogAccess = Depends(get_dog_access),
) -> RemoveCareTaskCommandHandler:
    return RemoveCareTaskCommandHandler(tasks, access)
