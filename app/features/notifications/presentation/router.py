from fastapi import APIRouter, Depends, Query

from app.core.response import APIResponse
from app.features.auth.presentation.dependencies import get_actor
from app.features.notifications.application.commands.mark_all_notifications_read.mark_all_notifications_read_command import (
    MarkAllNotificationsReadCommand,
)
from app.features.notifications.application.commands.mark_all_notifications_read.mark_all_notifications_read_command_handler import (
    MarkAllNotificationsReadCommandHandler,
)
from app.features.notifications.application.commands.mark_notification_read.mark_notification_read_command import (
    MarkNotificationReadCommand,
)
from app.features.notifications.application.commands.mark_notification_read.mark_notification_read_command_handler import (
    MarkNotificationReadCommandHandler,
)
from app.features.notifications.application.queries.get_inbox.get_inbox_query import GetInboxQuery
from app.features.notifications.application.queries.get_inbox.get_inbox_query_handler import (
    GetInboxQueryHandler,
)
from app.features.notifications.presentation.dependencies import (
    get_inbox_query_handler,
    get_mark_all_notifications_read_command_handler,
    get_mark_notification_read_command_handler,
)
from app.features.notifications.presentation.responses.inbox_response import InboxResponse
from app.features.notifications.presentation.responses.unread_count_response import (
    UnreadCountResponse,
)
from app.shared.actor import Actor

router = APIRouter()


@router.get("", response_model=APIResponse[InboxResponse], summary="List my notifications")
async def get_inbox(
    limit: int = Query(100, ge=1, le=200),
    actor: Actor = Depends(get_actor),
    handler: GetInboxQueryHandler = Depends(get_inbox_query_handler),
) -> APIResponse[InboxResponse]:
    inbox = await handler.handle(GetInboxQuery(actor=actor, limit=limit))
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
    handler: MarkAllNotificationsReadCommandHandler = Depends(
        get_mark_all_notifications_read_command_handler
    ),
) -> APIResponse[UnreadCountResponse]:
    unread = await handler.handle(MarkAllNotificationsReadCommand(actor=actor))
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
    handler: MarkNotificationReadCommandHandler = Depends(
        get_mark_notification_read_command_handler
    ),
) -> APIResponse[UnreadCountResponse]:
    unread = await handler.handle(
        MarkNotificationReadCommand(actor=actor, notification_id=notification_id)
    )
    return APIResponse(
        message="Notification marked read", data=UnreadCountResponse(unread_count=unread)
    )
