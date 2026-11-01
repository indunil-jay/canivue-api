from app.features.community.application.commands.share_post.share_post_command import (
    SharePostCommand,
)
from app.features.community.application.dtos.post_view import PostView
from app.features.community.application.interfaces.repositories.community_repository import (
    CommunityRepositoryProtocol,
)
from app.features.community.application.services.post_views import PostViews
from app.features.community.domain.exceptions import PostNotFoundError


class SharePostCommandHandler:
    def __init__(self, repo: CommunityRepositoryProtocol, views: PostViews):
        self._repo = repo
        self._views = views

    async def handle(self, command: SharePostCommand) -> PostView:
        if await self._repo.get_post(command.post_id) is None:
            raise PostNotFoundError()
        await self._repo.increment_shares(command.post_id)
        return await self._views.one(command.actor, command.post_id)
