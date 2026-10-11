from collections.abc import Sequence

from app.features.dogs.application.services.dog_access import DogAccess
from app.features.medical_records.application.interfaces.repositories.medical_record_repository import (
    MedicalRecordRepositoryProtocol,
)
from app.features.medical_records.application.queries.list_medical_records.list_medical_records_query import (
    ListMedicalRecordsQuery,
)
from app.features.medical_records.domain.entities.medical_record import MedicalRecord


class ListMedicalRecordsQueryHandler:
    def __init__(self, records: MedicalRecordRepositoryProtocol, access: DogAccess):
        self._records = records
        self._access = access

    async def handle(self, query: ListMedicalRecordsQuery) -> Sequence[MedicalRecord]:
        dog = await self._access.readable(query.actor, query.dog_id)
        return await self._records.list_for_dog(dog.id)
