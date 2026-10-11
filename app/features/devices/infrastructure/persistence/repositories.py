from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.dataclass_repository import DataclassRepository
from app.core.models import UtcDateTime, UuidTimestampMixin
from app.features.devices.domain.entities import (
    SmartCollar,
    SmartCollarRepositoryProtocol,
    SyncEvent,
)


class SmartCollarModel(UuidTimestampMixin, Base):
    __tablename__ = "smart_collars"

    dog_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    battery_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    firmware_version: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    sync_history: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    granted_permissions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)


class SqlAlchemySmartCollarRepository(
    DataclassRepository[SmartCollar, SmartCollarModel], SmartCollarRepositoryProtocol
):
    _model_cls = SmartCollarModel
    _entity_cls = SmartCollar

    def _to_entity(self, model: SmartCollarModel) -> SmartCollar:
        collar = super()._to_entity(model)
        collar.sync_history = [
            SyncEvent(datetime.fromisoformat(e["timestamp"]), e["records_synced"])
            for e in model.sync_history
        ]
        return collar

    def _to_model_dict(self, entity: SmartCollar) -> dict[str, Any]:
        data = super()._to_model_dict(entity)
        data["sync_history"] = [
            {"timestamp": e.timestamp.isoformat(), "records_synced": e.records_synced}
            for e in entity.sync_history
        ]
        return data

    async def get_for_dog(self, dog_id: str) -> SmartCollar | None:
        return await self.find_one(SmartCollarModel.dog_id == dog_id)

    async def save(self, collar: SmartCollar) -> SmartCollar:
        if await self.get_by_id(collar.id) is None:
            return await self.create(collar)
        return await self.update(collar)
