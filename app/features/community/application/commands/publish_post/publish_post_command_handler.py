from app.features.community.application.commands.publish_post.publish_post_command import (
    PublishPostCommand,
)
from app.features.community.application.interfaces.repositories.community_repository import (
    CommunityRepositoryProtocol,
)
from app.features.community.application.services.post_views import PostViews
from app.features.community.domain.entities.community_post import CommunityPost
from app.features.community.domain.exceptions import CommunityNotFoundError
from app.features.community.domain.value_objects.post_view import PostView


class PublishPostCommandHandler:
    def __init__(self, repo: CommunityRepositoryProtocol, views: PostViews):
        self._repo = repo
        self._views = views

    async def handle(self, command: PublishPostCommand) -> PostView:
        community = await self._repo.get_community(command.community_id)
        if community is None:
            raise CommunityNotFoundError()
        post = await self._repo.add_post(
            CommunityPost(
                author_id=command.actor.id,
                author_name=command.actor.display_name,
                is_veterinarian=command.actor.is_vet,
                community_id=community.id,
                community_tag=community.name,
                content=command.content.strip(),
            )
        )
        return await self._views.one(command.actor, post.id)
