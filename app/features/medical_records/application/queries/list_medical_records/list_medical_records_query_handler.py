from app.features.dogs.application.services.dog_access import DogAccess
from app.features.medical_records.application.dtos.medical_record_output_dto import (
    MedicalRecordOutputDTO,
)
from app.features.medical_records.application.interfaces.repositories.medical_record_repository import (
    MedicalRecordRepositoryProtocol,
)
from app.features.medical_records.application.mappers.medical_record_dto_mapper import (
    MedicalRecordDTOMapper,
)
from app.features.medical_records.application.queries.list_medical_records.list_medical_records_query import (
    ListMedicalRecordsQuery,
)


class ListMedicalRecordsQueryHandler:
    def __init__(self, records: MedicalRecordRepositoryProtocol, access: DogAccess):
        self._records = records
        self._access = access

    async def handle(self, query: ListMedicalRecordsQuery) -> list[MedicalRecordOutputDTO]:
        dog = await self._access.readable(query.actor, query.dog_id)
        return [
            MedicalRecordDTOMapper.to_output_dto(item)
            for item in await self._records.list_for_dog(dog.id)
        ]
