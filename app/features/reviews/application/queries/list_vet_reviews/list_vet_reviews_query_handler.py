from app.features.reviews.application.dtos.review_output_dto import ReviewOutputDTO
from app.features.reviews.application.interfaces.repositories.review_repository import (
    ReviewRepositoryProtocol,
)
from app.features.reviews.application.mappers.review_dto_mapper import ReviewDTOMapper
from app.features.reviews.application.queries.list_vet_reviews.list_vet_reviews_query import (
    ListVetReviewsQuery,
)
from app.features.veterinarians.application.interfaces.repositories.vet_profile_repository import (
    VetProfileRepositoryProtocol,
)
from app.features.veterinarians.domain.exceptions import VeterinarianNotFoundError


class ListVetReviewsQueryHandler:
    def __init__(self, reviews: ReviewRepositoryProtocol, vets: VetProfileRepositoryProtocol):
        self._reviews = reviews
        self._vets = vets

    async def handle(self, query: ListVetReviewsQuery) -> list[ReviewOutputDTO]:
        vet = await self._vets.get_by_id(query.vet_id)
        if vet is None or not vet.verified:
            raise VeterinarianNotFoundError()
        return [
            ReviewDTOMapper.to_output_dto(item) for item in await self._reviews.list_for_vet(vet.id)
        ]
