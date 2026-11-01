from app.features.appointments.application.dtos.appointment_output_dto import AppointmentOutputDTO
from app.features.appointments.domain.entities.appointment import Appointment


class AppointmentDTOMapper:
    @staticmethod
    def to_output_dto(entity: Appointment) -> AppointmentOutputDTO:
        return AppointmentOutputDTO(
            id=entity.id,
            owner_id=entity.owner_id,
            owner_name=entity.owner_name,
            vet_id=entity.vet_id,
            vet_user_id=entity.vet_user_id,
            vet_name=entity.vet_name,
            dog_id=entity.dog_id,
            dog_name=entity.dog_name,
            date_time=entity.date_time,
            status=entity.status,
            consultation_type=entity.consultation_type,
            fee_usd=entity.fee_usd,
            notes=entity.notes,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
