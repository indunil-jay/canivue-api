from fastapi import APIRouter, Depends, status

from app.core.response import APIResponse
from app.features.auth.presentation.dependencies import get_actor
from app.features.preventive_care.application.commands.add_care_task.add_care_task_command import (
    AddCareTaskCommand,
)
from app.features.preventive_care.application.commands.add_care_task.add_care_task_command_handler import (
    AddCareTaskCommandHandler,
)
from app.features.preventive_care.application.commands.complete_care_task.complete_care_task_command import (
    CompleteCareTaskCommand,
)
from app.features.preventive_care.application.commands.complete_care_task.complete_care_task_command_handler import (
    CompleteCareTaskCommandHandler,
)
from app.features.preventive_care.application.commands.remove_care_task.remove_care_task_command import (
    RemoveCareTaskCommand,
)
from app.features.preventive_care.application.commands.remove_care_task.remove_care_task_command_handler import (
    RemoveCareTaskCommandHandler,
)
from app.features.preventive_care.application.queries.list_care_tasks.list_care_tasks_query import (
    ListCareTasksQuery,
)
from app.features.preventive_care.application.queries.list_care_tasks.list_care_tasks_query_handler import (
    ListCareTasksQueryHandler,
)
from app.features.preventive_care.presentation.dependencies import (
    get_add_care_task_command_handler,
    get_complete_care_task_command_handler,
    get_list_care_tasks_query_handler,
    get_remove_care_task_command_handler,
)
from app.features.preventive_care.presentation.requests.add_care_task_request import (
    AddCareTaskRequest,
)
from app.features.preventive_care.presentation.responses.care_task_response import CareTaskResponse
from app.shared.actor import Actor

router = APIRouter()


One = APIResponse[CareTaskResponse]


@router.get(
    "/{dog_id}/care-tasks",
    response_model=APIResponse[list[CareTaskResponse]],
    summary="List a Dog's care tasks: outstanding first, soonest due first",
)
async def list_care_tasks(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    handler: ListCareTasksQueryHandler = Depends(get_list_care_tasks_query_handler),
) -> APIResponse[list[CareTaskResponse]]:
    tasks = await handler.handle(ListCareTasksQuery(actor=actor, dog_id=dog_id))
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
    handler: AddCareTaskCommandHandler = Depends(get_add_care_task_command_handler),
) -> One:
    task = await handler.handle(
        AddCareTaskCommand(
            actor=actor,
            dog_id=dog_id,
            category=payload.category,
            title=payload.title,
            due_date=payload.due_date,
        )
    )
    return APIResponse(message="Care task added", data=CareTaskResponse.model_validate(task))


@router.post(
    "/{dog_id}/care-tasks/{task_id}/complete", response_model=One, summary="Mark a care task done"
)
async def complete_care_task(
    dog_id: str,
    task_id: str,
    actor: Actor = Depends(get_actor),
    handler: CompleteCareTaskCommandHandler = Depends(get_complete_care_task_command_handler),
) -> One:
    task = await handler.handle(
        CompleteCareTaskCommand(actor=actor, dog_id=dog_id, task_id=task_id)
    )
    return APIResponse(message="Care task completed", data=CareTaskResponse.model_validate(task))


@router.delete(
    "/{dog_id}/care-tasks/{task_id}", response_model=APIResponse[None], summary="Remove a care task"
)
async def remove_care_task(
    dog_id: str,
    task_id: str,
    actor: Actor = Depends(get_actor),
    handler: RemoveCareTaskCommandHandler = Depends(get_remove_care_task_command_handler),
) -> APIResponse[None]:
    await handler.handle(RemoveCareTaskCommand(actor=actor, dog_id=dog_id, task_id=task_id))
    return APIResponse(message="Care task removed", data=None)
