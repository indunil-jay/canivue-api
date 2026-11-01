from app.features.reviews.application.dtos.review_output_dto import ReviewOutputDTO
from app.features.reviews.domain.entities.review import Review


class ReviewDTOMapper:
    @staticmethod
    def to_output_dto(entity: Review) -> ReviewOutputDTO:
        return ReviewOutputDTO(
            id=entity.id,
            appointment_id=entity.appointment_id,
            vet_id=entity.vet_id,
            owner_id=entity.owner_id,
            owner_name=entity.owner_name,
            rating=entity.rating,
            comment=entity.comment,
            date=entity.date,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
