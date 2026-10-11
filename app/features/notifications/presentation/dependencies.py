from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.features.notifications.application.commands.mark_all_notifications_read.mark_all_notifications_read_command_handler import (
    MarkAllNotificationsReadCommandHandler,
)
from app.features.notifications.application.commands.mark_notification_read.mark_notification_read_command_handler import (
    MarkNotificationReadCommandHandler,
)
from app.features.notifications.application.interfaces.repositories.notification_repository import (
    NotificationRepositoryProtocol,
)
from app.features.notifications.application.queries.get_inbox.get_inbox_query_handler import (
    GetInboxQueryHandler,
)
from app.features.notifications.application.services.stored_notifier import StoredNotifier
from app.features.notifications.infrastructure.persistence.repositories.notification_repository import (
    SqlAlchemyNotificationRepository,
)
from app.shared.notifier import NotifierProtocol


def get_notification_repository(
    session: AsyncSession = Depends(get_db_session),
) -> NotificationRepositoryProtocol:
    return SqlAlchemyNotificationRepository(session=session)


def get_notifier(
    notifications: NotificationRepositoryProtocol = Depends(get_notification_repository),
) -> NotifierProtocol:
    return StoredNotifier(notifications)


def get_inbox_query_handler(
    notifications: NotificationRepositoryProtocol = Depends(get_notification_repository),
) -> GetInboxQueryHandler:
    return GetInboxQueryHandler(notifications)


def get_mark_notification_read_command_handler(
    notifications: NotificationRepositoryProtocol = Depends(get_notification_repository),
) -> MarkNotificationReadCommandHandler:
    return MarkNotificationReadCommandHandler(notifications)


def get_mark_all_notifications_read_command_handler(
    notifications: NotificationRepositoryProtocol = Depends(get_notification_repository),
) -> MarkAllNotificationsReadCommandHandler:
    return MarkAllNotificationsReadCommandHandler(notifications)
