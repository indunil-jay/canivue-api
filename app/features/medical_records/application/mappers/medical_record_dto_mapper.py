from app.features.medical_records.application.dtos.medical_record_output_dto import (
    MedicalRecordOutputDTO,
)
from app.features.medical_records.domain.entities.medical_record import MedicalRecord


class MedicalRecordDTOMapper:
    @staticmethod
    def to_output_dto(entity: MedicalRecord) -> MedicalRecordOutputDTO:
        return MedicalRecordOutputDTO(
            id=entity.id,
            dog_id=entity.dog_id,
            type=entity.type,
            title=entity.title,
            description=entity.description,
            date=entity.date,
            file_id=entity.file_id,
            author_user_id=entity.author_user_id,
            author_name=entity.author_name,
            authored_by_vet=entity.authored_by_vet,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
