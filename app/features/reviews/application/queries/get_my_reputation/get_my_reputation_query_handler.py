from app.features.reviews.application.dtos.vet_reputation import VetReputation
from app.features.reviews.application.interfaces.repositories.review_repository import (
    ReviewRepositoryProtocol,
)
from app.features.reviews.application.mappers.review_dto_mapper import ReviewDTOMapper
from app.features.reviews.application.queries.get_my_reputation.get_my_reputation_query import (
    GetMyReputationQuery,
)
from app.features.veterinarians.application.interfaces.repositories.vet_profile_repository import (
    VetProfileRepositoryProtocol,
)
from app.features.veterinarians.application.interfaces.services.vet_stats_provider import (
    VetStatsProviderProtocol,
)
from app.features.veterinarians.domain.exceptions import VeterinarianNotFoundError


class GetMyReputationQueryHandler:
    def __init__(
        self,
        reviews: ReviewRepositoryProtocol,
        vets: VetProfileRepositoryProtocol,
        stats: VetStatsProviderProtocol,
    ):
        self._reviews = reviews
        self._vets = vets
        self._stats = stats

    async def handle(self, query: GetMyReputationQuery) -> VetReputation:
        vet = await self._vets.get_by_user_id(query.actor.id)
        if vet is None:
            raise VeterinarianNotFoundError()
        stats = (await self._stats.stats_for([vet.id]))[vet.id]
        return VetReputation(
            average_rating=stats.rating,
            total_consultations=stats.consultation_count,
            recommendations_accepted_percent=stats.recommendations_accepted_percent,
            repeat_consultation_percent=stats.follow_up_rate_percent,
            reviews=[
                ReviewDTOMapper.to_output_dto(r) for r in await self._reviews.list_for_vet(vet.id)
            ],
        )
