from collections.abc import Sequence

from sqlalchemy import update

from app.core.dataclass_repository import DataclassRepository
from app.features.notifications.application.interfaces.repositories.notification_repository import (
    NotificationRepositoryProtocol,
)
from app.features.notifications.domain.entities.notification import Notification
from app.features.notifications.infrastructure.persistence.models.notification_model import (
    NotificationModel,
)


class SqlAlchemyNotificationRepository(
    DataclassRepository[Notification, NotificationModel], NotificationRepositoryProtocol
):
    _model_cls = NotificationModel
    _entity_cls = Notification

    async def get_for_user(self, user_id: int, notification_id: str) -> Notification | None:
        return await self.find_one(
            NotificationModel.id == notification_id, NotificationModel.user_id == user_id
        )

    async def list_for_user(self, user_id: int, limit: int) -> Sequence[Notification]:
        return await self.find(
            NotificationModel.user_id == user_id,
            order_by=NotificationModel.created_at.desc(),
            limit=limit,
        )

    async def count_unread(self, user_id: int) -> int:
        return await self.count(
            NotificationModel.user_id == user_id, NotificationModel.is_read.is_(False)
        )

    async def mark_read(self, user_id: int, notification_id: str | None = None) -> None:
        stmt = update(NotificationModel).where(NotificationModel.user_id == user_id)
        if notification_id is not None:
            stmt = stmt.where(NotificationModel.id == notification_id)
        await self._session.execute(stmt.values(is_read=True))
        await self._session.flush()
