from fastapi import APIRouter, Depends, Query, status

from app.core.response import APIResponse
from app.features.auth.presentation.dependencies import get_actor
from app.features.community.application.commands.publish_post.publish_post_command import (
    PublishPostCommand,
)
from app.features.community.application.commands.publish_post.publish_post_command_handler import (
    PublishPostCommandHandler,
)
from app.features.community.application.commands.share_post.share_post_command import (
    SharePostCommand,
)
from app.features.community.application.commands.share_post.share_post_command_handler import (
    SharePostCommandHandler,
)
from app.features.community.application.commands.toggle_membership.toggle_membership_command import (
    ToggleMembershipCommand,
)
from app.features.community.application.commands.toggle_membership.toggle_membership_command_handler import (
    ToggleMembershipCommandHandler,
)
from app.features.community.application.commands.toggle_post_reaction.toggle_post_reaction_command import (
    TogglePostReactionCommand,
)
from app.features.community.application.commands.toggle_post_reaction.toggle_post_reaction_command_handler import (
    TogglePostReactionCommandHandler,
)
from app.features.community.application.queries.get_feed.get_feed_query import GetFeedQuery
from app.features.community.application.queries.get_feed.get_feed_query_handler import (
    GetFeedQueryHandler,
)
from app.features.community.application.queries.list_communities.list_communities_query import (
    ListCommunitiesQuery,
)
from app.features.community.application.queries.list_communities.list_communities_query_handler import (
    ListCommunitiesQueryHandler,
)
from app.features.community.domain.enums.reaction_kind import ReactionKind
from app.features.community.presentation.dependencies import (
    get_feed_query_handler,
    get_list_communities_query_handler,
    get_publish_post_command_handler,
    get_share_post_command_handler,
    get_toggle_membership_command_handler,
    get_toggle_post_reaction_command_handler,
)
from app.features.community.presentation.mappers import CommunityPresentationMapper
from app.features.community.presentation.requests.publish_post_request import PublishPostRequest
from app.features.community.presentation.responses.community_post_response import (
    CommunityPostResponse,
)
from app.features.community.presentation.responses.disease_community_response import (
    DiseaseCommunityResponse,
)
from app.shared.actor import Actor

router = APIRouter()


Post = APIResponse[CommunityPostResponse]


@router.get(
    "/feed",
    response_model=APIResponse[list[CommunityPostResponse]],
    summary="Read the community feed, newest first",
)
async def get_feed(
    community_id: str | None = None,
    saved: bool = Query(False, description="Only posts I have saved"),
    limit: int = Query(50, ge=1, le=100),
    actor: Actor = Depends(get_actor),
    handler: GetFeedQueryHandler = Depends(get_feed_query_handler),
) -> APIResponse[list[CommunityPostResponse]]:
    views = await handler.handle(
        GetFeedQuery(actor=actor, community_id=community_id, saved_only=saved, limit=limit)
    )
    return APIResponse(
        message="Feed retrieved successfully",
        data=[CommunityPresentationMapper.to_community_post_response(v) for v in views],
    )


@router.post(
    "/posts",
    response_model=Post,
    status_code=status.HTTP_201_CREATED,
    summary="Publish a post in a disease community",
)
async def publish_post(
    payload: PublishPostRequest,
    actor: Actor = Depends(get_actor),
    handler: PublishPostCommandHandler = Depends(get_publish_post_command_handler),
) -> Post:
    view = await handler.handle(
        PublishPostCommand(actor=actor, community_id=payload.community_id, content=payload.content)
    )
    return APIResponse(
        message="Post published", data=CommunityPresentationMapper.to_community_post_response(view)
    )


@router.post("/posts/{post_id}/like", response_model=Post, summary="Like or unlike a post")
async def toggle_like(
    post_id: str,
    actor: Actor = Depends(get_actor),
    handler: TogglePostReactionCommandHandler = Depends(get_toggle_post_reaction_command_handler),
) -> Post:
    view = await handler.handle(
        TogglePostReactionCommand(actor=actor, post_id=post_id, kind=ReactionKind.LIKE)
    )
    return APIResponse(
        message="Post updated", data=CommunityPresentationMapper.to_community_post_response(view)
    )


@router.post("/posts/{post_id}/save", response_model=Post, summary="Save or unsave a post")
async def toggle_save(
    post_id: str,
    actor: Actor = Depends(get_actor),
    handler: TogglePostReactionCommandHandler = Depends(get_toggle_post_reaction_command_handler),
) -> Post:
    view = await handler.handle(
        TogglePostReactionCommand(actor=actor, post_id=post_id, kind=ReactionKind.SAVE)
    )
    return APIResponse(
        message="Post updated", data=CommunityPresentationMapper.to_community_post_response(view)
    )


@router.post("/posts/{post_id}/share", response_model=Post, summary="Count a share of a post")
async def share_post(
    post_id: str,
    actor: Actor = Depends(get_actor),
    handler: SharePostCommandHandler = Depends(get_share_post_command_handler),
) -> Post:
    view = await handler.handle(SharePostCommand(actor=actor, post_id=post_id))
    return APIResponse(
        message="Share recorded", data=CommunityPresentationMapper.to_community_post_response(view)
    )


@router.get(
    "/communities",
    response_model=APIResponse[list[DiseaseCommunityResponse]],
    summary="List disease communities",
)
async def list_communities(
    actor: Actor = Depends(get_actor),
    handler: ListCommunitiesQueryHandler = Depends(get_list_communities_query_handler),
) -> APIResponse[list[DiseaseCommunityResponse]]:
    views = await handler.handle(ListCommunitiesQuery(actor=actor))
    return APIResponse(
        message="Communities retrieved successfully",
        data=[CommunityPresentationMapper.to_disease_community_response(v) for v in views],
    )


@router.post(
    "/communities/{community_id}/join",
    response_model=APIResponse[DiseaseCommunityResponse],
    summary="Join or leave a community",
)
async def toggle_join(
    community_id: str,
    actor: Actor = Depends(get_actor),
    handler: ToggleMembershipCommandHandler = Depends(get_toggle_membership_command_handler),
) -> APIResponse[DiseaseCommunityResponse]:
    view = await handler.handle(ToggleMembershipCommand(actor=actor, community_id=community_id))
    return APIResponse(
        message="Membership updated",
        data=CommunityPresentationMapper.to_disease_community_response(view),
    )
