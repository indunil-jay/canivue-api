from app.features.community.application.dtos.community_view import CommunityView
from app.features.community.application.interfaces.repositories.community_repository import (
    CommunityRepositoryProtocol,
)
from app.features.community.application.mappers.disease_community_dto_mapper import (
    DiseaseCommunityDTOMapper,
)
from app.features.community.application.queries.list_communities.list_communities_query import (
    ListCommunitiesQuery,
)


class ListCommunitiesQueryHandler:
    def __init__(self, repo: CommunityRepositoryProtocol):
        self._repo = repo

    async def handle(self, query: ListCommunitiesQuery) -> list[CommunityView]:
        counts = await self._repo.member_counts()
        joined = await self._repo.joined_ids(query.actor.id)
        return [
            CommunityView(
                DiseaseCommunityDTOMapper.to_output_dto(c), counts.get(c.id, 0), c.id in joined
            )
            for c in await self._repo.list_communities()
        ]
