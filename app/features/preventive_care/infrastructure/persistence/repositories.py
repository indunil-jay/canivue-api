from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.dataclass_repository import DataclassRepository
from app.core.models import UtcDateTime, UuidTimestampMixin
from app.features.preventive_care.domain.entities import CareTask, CareTaskRepositoryProtocol


class CareTaskModel(UuidTimestampMixin, Base):
    __tablename__ = "care_tasks"

    dog_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    due_date: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False, index=True)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)


class SqlAlchemyCareTaskRepository(
    DataclassRepository[CareTask, CareTaskModel], CareTaskRepositoryProtocol
):
    _model_cls = CareTaskModel
    _entity_cls = CareTask

    async def list_for_dog(self, dog_id: str) -> Sequence[CareTask]:
        return await self.find(
            CareTaskModel.dog_id == dog_id,
            order_by=[CareTaskModel.completed, CareTaskModel.due_date],
        )
