from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.response import APIResponse
from app.features.auth.presentation.dependencies import get_actor
from app.features.community.application.use_cases import (
    GetFeedUseCase,
    ListCommunitiesUseCase,
    PostViews,
    PublishPostUseCase,
    SharePostUseCase,
    ToggleMembershipUseCase,
    TogglePostReactionUseCase,
)
from app.features.community.domain.entities import (
    CommunityRepositoryProtocol,
    CommunityView,
    PostView,
    ReactionKind,
)
from app.features.community.infrastructure.persistence.repositories import (
    SqlAlchemyCommunityRepository,
)
from app.shared.actor import Actor
from app.shared.text import initials_of

router = APIRouter()


class PublishPostRequest(BaseModel):
    community_id: str
    content: str = Field(..., min_length=1, max_length=5000)


class CommunityPostResponse(BaseModel):
    id: str
    author_name: str
    author_initials: str
    is_veterinarian: bool
    community_id: str
    community_tag: str
    content: str
    created_at: datetime
    like_count: int
    comment_count: int = Field(0, description="Comments are not supported yet; always 0.")
    share_count: int
    liked_by_me: bool
    saved_by_me: bool

    @classmethod
    def of(cls, view: PostView) -> "CommunityPostResponse":
        p = view.post
        return cls(
            id=p.id,
            author_name=p.author_name,
            author_initials=initials_of(p.author_name),
            is_veterinarian=p.is_veterinarian,
            community_id=p.community_id,
            community_tag=p.community_tag,
            content=p.content,
            created_at=p.created_at,
            like_count=view.like_count,
            share_count=p.share_count,
            liked_by_me=view.liked_by_me,
            saved_by_me=view.saved_by_me,
        )


class DiseaseCommunityResponse(BaseModel):
    id: str
    name: str
    description: str
    member_count: int
    joined: bool

    @classmethod
    def of(cls, view: CommunityView) -> "DiseaseCommunityResponse":
        c = view.community
        return cls(
            id=c.id,
            name=c.name,
            description=c.description,
            member_count=view.member_count,
            joined=view.joined,
        )


Post = APIResponse[CommunityPostResponse]


def get_community_repository(
    session: AsyncSession = Depends(get_db_session),
) -> CommunityRepositoryProtocol:
    return SqlAlchemyCommunityRepository(session)


def get_post_views(
    repo: CommunityRepositoryProtocol = Depends(get_community_repository),
) -> PostViews:
    return PostViews(repo)


def _with_views(use_case_cls):
    def provide(
        repo: CommunityRepositoryProtocol = Depends(get_community_repository),
        views: PostViews = Depends(get_post_views),
    ):
        return use_case_cls(repo, views)

    return provide


def _with_repo(use_case_cls):
    def provide(repo: CommunityRepositoryProtocol = Depends(get_community_repository)):
        return use_case_cls(repo)

    return provide


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
    use_case: GetFeedUseCase = Depends(_with_views(GetFeedUseCase)),
) -> APIResponse[list[CommunityPostResponse]]:
    views = await use_case.execute(actor, community_id, saved, limit)
    return APIResponse(
        message="Feed retrieved successfully", data=[CommunityPostResponse.of(v) for v in views]
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
    use_case: PublishPostUseCase = Depends(_with_views(PublishPostUseCase)),
) -> Post:
    view = await use_case.execute(actor, payload.community_id, payload.content)
    return APIResponse(message="Post published", data=CommunityPostResponse.of(view))


@router.post("/posts/{post_id}/like", response_model=Post, summary="Like or unlike a post")
async def toggle_like(
    post_id: str,
    actor: Actor = Depends(get_actor),
    use_case: TogglePostReactionUseCase = Depends(_with_views(TogglePostReactionUseCase)),
) -> Post:
    view = await use_case.execute(actor, post_id, ReactionKind.LIKE)
    return APIResponse(message="Post updated", data=CommunityPostResponse.of(view))


@router.post("/posts/{post_id}/save", response_model=Post, summary="Save or unsave a post")
async def toggle_save(
    post_id: str,
    actor: Actor = Depends(get_actor),
    use_case: TogglePostReactionUseCase = Depends(_with_views(TogglePostReactionUseCase)),
) -> Post:
    view = await use_case.execute(actor, post_id, ReactionKind.SAVE)
    return APIResponse(message="Post updated", data=CommunityPostResponse.of(view))


@router.post("/posts/{post_id}/share", response_model=Post, summary="Count a share of a post")
async def share_post(
    post_id: str,
    actor: Actor = Depends(get_actor),
    use_case: SharePostUseCase = Depends(_with_views(SharePostUseCase)),
) -> Post:
    view = await use_case.execute(actor, post_id)
    return APIResponse(message="Share recorded", data=CommunityPostResponse.of(view))


@router.get(
    "/communities",
    response_model=APIResponse[list[DiseaseCommunityResponse]],
    summary="List disease communities",
)
async def list_communities(
    actor: Actor = Depends(get_actor),
    use_case: ListCommunitiesUseCase = Depends(_with_repo(ListCommunitiesUseCase)),
) -> APIResponse[list[DiseaseCommunityResponse]]:
    views = await use_case.execute(actor)
    return APIResponse(
        message="Communities retrieved successfully",
        data=[DiseaseCommunityResponse.of(v) for v in views],
    )


@router.post(
    "/communities/{community_id}/join",
    response_model=APIResponse[DiseaseCommunityResponse],
    summary="Join or leave a community",
)
async def toggle_join(
    community_id: str,
    actor: Actor = Depends(get_actor),
    use_case: ToggleMembershipUseCase = Depends(_with_repo(ToggleMembershipUseCase)),
) -> APIResponse[DiseaseCommunityResponse]:
    view = await use_case.execute(actor, community_id)
    return APIResponse(message="Membership updated", data=DiseaseCommunityResponse.of(view))
