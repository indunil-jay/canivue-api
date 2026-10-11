from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field

from app.core.response import APIResponse
from app.features.auth.presentation.dependencies import get_actor
from app.features.notifications.application.use_cases import (
    GetInboxUseCase,
    MarkAllNotificationsReadUseCase,
    MarkNotificationReadUseCase,
)
from app.features.notifications.presentation.dependencies import (
    get_inbox_use_case,
    get_mark_all_notifications_read_use_case,
    get_mark_notification_read_use_case,
)
from app.shared.actor import Actor
from app.shared.notifier import NotificationType

router = APIRouter()


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    title: str
    message: str
    timestamp: datetime = Field(validation_alias="created_at")
    type: NotificationType
    dog_name: str
    is_read: bool
    action_label: str | None


class InboxResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[NotificationResponse]
    unread_count: int


class UnreadCountResponse(BaseModel):
    unread_count: int


@router.get("", response_model=APIResponse[InboxResponse], summary="List my notifications")
async def get_inbox(
    limit: int = Query(100, ge=1, le=200),
    actor: Actor = Depends(get_actor),
    use_case: GetInboxUseCase = Depends(get_inbox_use_case),
) -> APIResponse[InboxResponse]:
    inbox = await use_case.execute(actor, limit)
    return APIResponse(
        message="Notifications retrieved successfully", data=InboxResponse.model_validate(inbox)
    )


@router.post(
    "/read-all",
    response_model=APIResponse[UnreadCountResponse],
    summary="Mark all my notifications read",
)
async def mark_all_read(
    actor: Actor = Depends(get_actor),
    use_case: MarkAllNotificationsReadUseCase = Depends(get_mark_all_notifications_read_use_case),
) -> APIResponse[UnreadCountResponse]:
    unread = await use_case.execute(actor)
    return APIResponse(
        message="All notifications marked read", data=UnreadCountResponse(unread_count=unread)
    )


@router.post(
    "/{notification_id}/read",
    response_model=APIResponse[UnreadCountResponse],
    summary="Mark one notification read",
)
async def mark_read(
    notification_id: str,
    actor: Actor = Depends(get_actor),
    use_case: MarkNotificationReadUseCase = Depends(get_mark_notification_read_use_case),
) -> APIResponse[UnreadCountResponse]:
    unread = await use_case.execute(actor, notification_id)
    return APIResponse(
        message="Notification marked read", data=UnreadCountResponse(unread_count=unread)
    )
