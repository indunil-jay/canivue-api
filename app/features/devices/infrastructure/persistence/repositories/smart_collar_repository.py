from datetime import datetime
from typing import Any

from app.core.dataclass_repository import DataclassRepository
from app.features.devices.application.interfaces.repositories.smart_collar_repository import (
    SmartCollarRepositoryProtocol,
)
from app.features.devices.domain.entities.smart_collar import SmartCollar
from app.features.devices.domain.value_objects.sync_event import SyncEvent
from app.features.devices.infrastructure.persistence.models.smart_collar_model import (
    SmartCollarModel,
)


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
