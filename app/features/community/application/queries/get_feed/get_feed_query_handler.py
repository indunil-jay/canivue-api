from app.features.community.application.dtos.post_view import PostView
from app.features.community.application.interfaces.repositories.community_repository import (
    CommunityRepositoryProtocol,
)
from app.features.community.application.queries.get_feed.get_feed_query import GetFeedQuery
from app.features.community.application.services.post_views import PostViews


class GetFeedQueryHandler:
    def __init__(self, repo: CommunityRepositoryProtocol, views: PostViews):
        self._repo = repo
        self._views = views

    async def handle(self, query: GetFeedQuery) -> list[PostView]:
        posts = await self._repo.list_posts(
            query.community_id,
            saved_by=query.actor.id if query.saved_only else None,
            limit=query.limit,
        )
        return await self._views.of(query.actor, posts)
