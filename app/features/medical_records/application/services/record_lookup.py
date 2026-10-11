from app.features.dogs.application.services.dog_access import DogAccess
from app.features.medical_records.application.interfaces.repositories.medical_record_repository import (
    MedicalRecordRepositoryProtocol,
)
from app.features.medical_records.domain.entities.medical_record import MedicalRecord
from app.features.medical_records.domain.exceptions import MedicalRecordNotFoundError
from app.shared.actor import Actor


class _RecordLookup:
    def __init__(self, records: MedicalRecordRepositoryProtocol, access: DogAccess):
        self._records = records
        self._access = access

    async def _load(self, actor: Actor, dog_id: str, record_id: str) -> MedicalRecord:
        dog = await self._access.readable(actor, dog_id)
        record = await self._records.get_by_id(record_id)
        if record is None or record.dog_id != dog.id:
            raise MedicalRecordNotFoundError()
        return record
