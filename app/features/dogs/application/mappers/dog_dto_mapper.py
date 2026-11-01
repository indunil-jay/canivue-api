from app.features.dogs.application.dtos.dog_output_dto import DogOutputDTO
from app.features.dogs.domain.entities.dog import Dog


class DogDTOMapper:
    @staticmethod
    def to_output_dto(entity: Dog) -> DogOutputDTO:
        return DogOutputDTO(
            id=entity.id,
            owner_id=entity.owner_id,
            name=entity.name,
            breed=entity.breed,
            birth_date=entity.birth_date,
            gender=entity.gender,
            weight_kg=entity.weight_kg,
            color=entity.color,
            microchip_id=entity.microchip_id,
            avatar_emoji=entity.avatar_emoji,
            is_neutered=entity.is_neutered,
            blood_group=entity.blood_group,
            primary_vet=entity.primary_vet,
            special_notes=entity.special_notes,
            allergies=entity.allergies,
            existing_conditions=entity.existing_conditions,
            vaccinations=entity.vaccinations,
            medications=entity.medications,
            insurance=entity.insurance,
            photo_file_id=entity.photo_file_id,
            is_archived=entity.is_archived,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            age_years=entity.age_years,
            age_months=entity.age_months,
            age_formatted=entity.age_formatted,
        )
