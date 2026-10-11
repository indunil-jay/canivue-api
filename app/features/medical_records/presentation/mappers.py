from app.features.medical_records.domain.entities.medical_record import MedicalRecord
from app.features.medical_records.presentation.responses.medical_record_response import (
    MedicalRecordResponse,
)


class MedicalRecordsPresentationMapper:
    @staticmethod
    def to_medical_record_response(record: MedicalRecord) -> MedicalRecordResponse:
        return MedicalRecordResponse(
            id=record.id,
            dog_id=record.dog_id,
            type=record.type,
            title=record.title,
            description=record.description,
            date=record.date,
            attachment_url=(
                f"/api/v1/dogs/{record.dog_id}/records/{record.id}/attachment"
                if record.file_id
                else None
            ),
            author_name=record.author_name,
            authored_by_vet=record.authored_by_vet,
        )
