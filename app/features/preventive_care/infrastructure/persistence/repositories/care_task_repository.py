from collections.abc import Sequence

from app.core.dataclass_repository import DataclassRepository
from app.features.preventive_care.application.interfaces.repositories.care_task_repository import (
    CareTaskRepositoryProtocol,
)
from app.features.preventive_care.domain.entities.care_task import CareTask
from app.features.preventive_care.infrastructure.persistence.models.care_task_model import (
    CareTaskModel,
)


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
