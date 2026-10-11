from datetime import datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.response import APIResponse
from app.features.auth.presentation.dependencies import get_actor
from app.features.dogs.application.access import DogAccess
from app.features.dogs.presentation.dependencies import get_dog_access
from app.features.preventive_care.application.use_cases import (
    AddCareTaskUseCase,
    CompleteCareTaskUseCase,
    ListCareTasksUseCase,
    RemoveCareTaskUseCase,
)
from app.features.preventive_care.domain.entities import (
    CareTaskCategory,
    CareTaskRepositoryProtocol,
)
from app.features.preventive_care.infrastructure.persistence.repositories import (
    SqlAlchemyCareTaskRepository,
)
from app.shared.actor import Actor

router = APIRouter()


class AddCareTaskRequest(BaseModel):
    category: CareTaskCategory
    title: str = Field(..., min_length=1, max_length=255)
    due_date: datetime


class CareTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    dog_id: str
    category: CareTaskCategory
    title: str
    due_date: datetime
    completed: bool
    completed_at: datetime | None
    is_overdue: bool


One = APIResponse[CareTaskResponse]


def get_care_task_repository(
    session: AsyncSession = Depends(get_db_session),
) -> CareTaskRepositoryProtocol:
    return SqlAlchemyCareTaskRepository(session=session)


def get_list_care_tasks_use_case(
    tasks: CareTaskRepositoryProtocol = Depends(get_care_task_repository),
    access: DogAccess = Depends(get_dog_access),
) -> ListCareTasksUseCase:
    return ListCareTasksUseCase(tasks, access)


def get_add_care_task_use_case(
    tasks: CareTaskRepositoryProtocol = Depends(get_care_task_repository),
    access: DogAccess = Depends(get_dog_access),
) -> AddCareTaskUseCase:
    return AddCareTaskUseCase(tasks, access)


def get_complete_care_task_use_case(
    tasks: CareTaskRepositoryProtocol = Depends(get_care_task_repository),
    access: DogAccess = Depends(get_dog_access),
) -> CompleteCareTaskUseCase:
    return CompleteCareTaskUseCase(tasks, access)


def get_remove_care_task_use_case(
    tasks: CareTaskRepositoryProtocol = Depends(get_care_task_repository),
    access: DogAccess = Depends(get_dog_access),
) -> RemoveCareTaskUseCase:
    return RemoveCareTaskUseCase(tasks, access)


@router.get(
    "/{dog_id}/care-tasks",
    response_model=APIResponse[list[CareTaskResponse]],
    summary="List a Dog's care tasks: outstanding first, soonest due first",
)
async def list_care_tasks(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    use_case: ListCareTasksUseCase = Depends(get_list_care_tasks_use_case),
) -> APIResponse[list[CareTaskResponse]]:
    tasks = await use_case.execute(actor, dog_id)
    return APIResponse(
        message="Care tasks retrieved successfully",
        data=[CareTaskResponse.model_validate(t) for t in tasks],
    )


@router.post(
    "/{dog_id}/care-tasks",
    response_model=One,
    status_code=status.HTTP_201_CREATED,
    summary="Add a care task",
)
async def add_care_task(
    dog_id: str,
    payload: AddCareTaskRequest,
    actor: Actor = Depends(get_actor),
    use_case: AddCareTaskUseCase = Depends(get_add_care_task_use_case),
) -> One:
    task = await use_case.execute(actor, dog_id, payload.category, payload.title, payload.due_date)
    return APIResponse(message="Care task added", data=CareTaskResponse.model_validate(task))


@router.post(
    "/{dog_id}/care-tasks/{task_id}/complete", response_model=One, summary="Mark a care task done"
)
async def complete_care_task(
    dog_id: str,
    task_id: str,
    actor: Actor = Depends(get_actor),
    use_case: CompleteCareTaskUseCase = Depends(get_complete_care_task_use_case),
) -> One:
    task = await use_case.execute(actor, dog_id, task_id)
    return APIResponse(message="Care task completed", data=CareTaskResponse.model_validate(task))


@router.delete(
    "/{dog_id}/care-tasks/{task_id}", response_model=APIResponse[None], summary="Remove a care task"
)
async def remove_care_task(
    dog_id: str,
    task_id: str,
    actor: Actor = Depends(get_actor),
    use_case: RemoveCareTaskUseCase = Depends(get_remove_care_task_use_case),
) -> APIResponse[None]:
    await use_case.execute(actor, dog_id, task_id)
    return APIResponse(message="Care task removed", data=None)
