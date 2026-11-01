from app.features.veterinarians.application.dtos.vet_profile_output_dto import VetProfileOutputDTO
from app.features.veterinarians.domain.entities.vet_profile import VetProfile


class VetProfileDTOMapper:
    @staticmethod
    def to_output_dto(entity: VetProfile) -> VetProfileOutputDTO:
        return VetProfileOutputDTO(
            id=entity.id,
            user_id=entity.user_id,
            name=entity.name,
            verified=entity.verified,
            specialty=entity.specialty,
            specialties=entity.specialties,
            experience_years=entity.experience_years,
            consultation_fee_usd=entity.consultation_fee_usd,
            response_time_minutes=entity.response_time_minutes,
            languages=entity.languages,
            consultation_types=entity.consultation_types,
            bio=entity.bio,
            clinics=entity.clinics,
            qualifications=entity.qualifications,
            availability=entity.availability,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
