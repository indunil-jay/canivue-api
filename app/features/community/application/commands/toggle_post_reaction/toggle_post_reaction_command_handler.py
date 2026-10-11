from app.features.community.application.commands.toggle_post_reaction.toggle_post_reaction_command import (
    TogglePostReactionCommand,
)
from app.features.community.application.interfaces.repositories.community_repository import (
    CommunityRepositoryProtocol,
)
from app.features.community.application.services.post_views import PostViews
from app.features.community.domain.exceptions import PostNotFoundError
from app.features.community.domain.value_objects.post_view import PostView


class TogglePostReactionCommandHandler:
    def __init__(self, repo: CommunityRepositoryProtocol, views: PostViews):
        self._repo = repo
        self._views = views

    async def handle(self, command: TogglePostReactionCommand) -> PostView:
        if await self._repo.get_post(command.post_id) is None:
            raise PostNotFoundError()
        await self._repo.toggle_reaction(command.post_id, command.actor.id, command.kind)
        return await self._views.one(command.actor, command.post_id)
