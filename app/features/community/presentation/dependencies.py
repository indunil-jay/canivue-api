from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.features.community.application.commands.publish_post.publish_post_command_handler import (
    PublishPostCommandHandler,
)
from app.features.community.application.commands.share_post.share_post_command_handler import (
    SharePostCommandHandler,
)
from app.features.community.application.commands.toggle_membership.toggle_membership_command_handler import (
    ToggleMembershipCommandHandler,
)
from app.features.community.application.commands.toggle_post_reaction.toggle_post_reaction_command_handler import (
    TogglePostReactionCommandHandler,
)
from app.features.community.application.interfaces.repositories.community_repository import (
    CommunityRepositoryProtocol,
)
from app.features.community.application.queries.get_feed.get_feed_query_handler import (
    GetFeedQueryHandler,
)
from app.features.community.application.queries.list_communities.list_communities_query_handler import (
    ListCommunitiesQueryHandler,
)
from app.features.community.application.services.post_views import PostViews
from app.features.community.infrastructure.persistence.repositories.community_repository import (
    SqlAlchemyCommunityRepository,
)


def get_community_repository(
    session: AsyncSession = Depends(get_db_session),
) -> CommunityRepositoryProtocol:
    return SqlAlchemyCommunityRepository(session)


def get_post_views(
    repo: CommunityRepositoryProtocol = Depends(get_community_repository),
) -> PostViews:
    return PostViews(repo)


def get_feed_query_handler(
    repo: CommunityRepositoryProtocol = Depends(get_community_repository),
    views: PostViews = Depends(get_post_views),
) -> GetFeedQueryHandler:
    return GetFeedQueryHandler(repo, views)


def get_publish_post_command_handler(
    repo: CommunityRepositoryProtocol = Depends(get_community_repository),
    views: PostViews = Depends(get_post_views),
) -> PublishPostCommandHandler:
    return PublishPostCommandHandler(repo, views)


def get_share_post_command_handler(
    repo: CommunityRepositoryProtocol = Depends(get_community_repository),
    views: PostViews = Depends(get_post_views),
) -> SharePostCommandHandler:
    return SharePostCommandHandler(repo, views)


def get_toggle_post_reaction_command_handler(
    repo: CommunityRepositoryProtocol = Depends(get_community_repository),
    views: PostViews = Depends(get_post_views),
) -> TogglePostReactionCommandHandler:
    return TogglePostReactionCommandHandler(repo, views)


def get_list_communities_query_handler(
    repo: CommunityRepositoryProtocol = Depends(get_community_repository),
) -> ListCommunitiesQueryHandler:
    return ListCommunitiesQueryHandler(repo)


def get_toggle_membership_command_handler(
    repo: CommunityRepositoryProtocol = Depends(get_community_repository),
) -> ToggleMembershipCommandHandler:
    return ToggleMembershipCommandHandler(repo)
