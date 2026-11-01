from collections.abc import Sequence

from app.core.dataclass_repository import DataclassRepository
from app.features.medical_records.application.interfaces.repositories.medical_record_repository import (
    MedicalRecordRepositoryProtocol,
)
from app.features.medical_records.domain.entities.medical_record import MedicalRecord
from app.features.medical_records.infrastructure.persistence.models.medical_record_model import (
    MedicalRecordModel,
)


class SqlAlchemyMedicalRecordRepository(
    DataclassRepository[MedicalRecord, MedicalRecordModel], MedicalRecordRepositoryProtocol
):
    _model_cls = MedicalRecordModel
    _entity_cls = MedicalRecord

    async def list_for_dog(self, dog_id: str) -> Sequence[MedicalRecord]:
        return await self.find(
            MedicalRecordModel.dog_id == dog_id,
            order_by=[MedicalRecordModel.date.desc(), MedicalRecordModel.created_at.desc()],
        )
