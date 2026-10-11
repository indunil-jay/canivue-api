from app.features.community.application.interfaces.repositories.community_repository import (
    CommunityRepositoryProtocol,
)
from app.features.community.application.queries.list_communities.list_communities_query import (
    ListCommunitiesQuery,
)
from app.features.community.domain.value_objects.community_view import CommunityView


class ListCommunitiesQueryHandler:
    def __init__(self, repo: CommunityRepositoryProtocol):
        self._repo = repo

    async def handle(self, query: ListCommunitiesQuery) -> list[CommunityView]:
        counts = await self._repo.member_counts()
        joined = await self._repo.joined_ids(query.actor.id)
        return [
            CommunityView(c, counts.get(c.id, 0), c.id in joined)
            for c in await self._repo.list_communities()
        ]
