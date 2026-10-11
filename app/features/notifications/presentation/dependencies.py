from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.features.notifications.application.use_cases import (
    GetInboxUseCase,
    MarkAllNotificationsReadUseCase,
    MarkNotificationReadUseCase,
    StoredNotifier,
)
from app.features.notifications.domain.repositories import NotificationRepositoryProtocol
from app.features.notifications.infrastructure.persistence.repositories import (
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


def get_inbox_use_case(
    notifications: NotificationRepositoryProtocol = Depends(get_notification_repository),
) -> GetInboxUseCase:
    return GetInboxUseCase(notifications)


def get_mark_notification_read_use_case(
    notifications: NotificationRepositoryProtocol = Depends(get_notification_repository),
) -> MarkNotificationReadUseCase:
    return MarkNotificationReadUseCase(notifications)


def get_mark_all_notifications_read_use_case(
    notifications: NotificationRepositoryProtocol = Depends(get_notification_repository),
) -> MarkAllNotificationsReadUseCase:
    return MarkAllNotificationsReadUseCase(notifications)
