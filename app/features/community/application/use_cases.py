from collections.abc import Sequence

from app.features.community.domain.entities import (
    CommunityNotFoundError,
    CommunityPost,
    CommunityRepositoryProtocol,
    CommunityView,
    PostNotFoundError,
    PostView,
    ReactionKind,
)
from app.shared.actor import Actor


class PostViews:
    def __init__(self, repo: CommunityRepositoryProtocol):
        self._repo = repo

    async def of(self, actor: Actor, posts: Sequence[CommunityPost]) -> list[PostView]:
        ids = [p.id for p in posts]
        likes = await self._repo.like_counts(ids)
        mine = await self._repo.reactions_of(actor.id, ids)
        return [
            PostView(
                post=p,
                like_count=likes.get(p.id, 0),
                liked_by_me=(p.id, ReactionKind.LIKE.value) in mine,
                saved_by_me=(p.id, ReactionKind.SAVE.value) in mine,
            )
            for p in posts
        ]

    async def one(self, actor: Actor, post_id: str) -> PostView:
        post = await self._repo.get_post(post_id)
        if post is None:
            raise PostNotFoundError()
        return (await self.of(actor, [post]))[0]


class GetFeedUseCase:
    def __init__(self, repo: CommunityRepositoryProtocol, views: PostViews):
        self._repo = repo
        self._views = views

    async def execute(
        self, actor: Actor, community_id: str | None, saved_only: bool, limit: int
    ) -> list[PostView]:
        posts = await self._repo.list_posts(
            community_id, saved_by=actor.id if saved_only else None, limit=limit
        )
        return await self._views.of(actor, posts)


class PublishPostUseCase:
    def __init__(self, repo: CommunityRepositoryProtocol, views: PostViews):
        self._repo = repo
        self._views = views

    async def execute(self, actor: Actor, community_id: str, content: str) -> PostView:
        community = await self._repo.get_community(community_id)
        if community is None:
            raise CommunityNotFoundError()
        post = await self._repo.add_post(
            CommunityPost(
                author_id=actor.id,
                author_name=actor.display_name,
                is_veterinarian=actor.is_vet,
                community_id=community.id,
                community_tag=community.name,
                content=content.strip(),
            )
        )
        return await self._views.one(actor, post.id)


class TogglePostReactionUseCase:
    def __init__(self, repo: CommunityRepositoryProtocol, views: PostViews):
        self._repo = repo
        self._views = views

    async def execute(self, actor: Actor, post_id: str, kind: ReactionKind) -> PostView:
        if await self._repo.get_post(post_id) is None:
            raise PostNotFoundError()
        await self._repo.toggle_reaction(post_id, actor.id, kind)
        return await self._views.one(actor, post_id)


class SharePostUseCase:
    def __init__(self, repo: CommunityRepositoryProtocol, views: PostViews):
        self._repo = repo
        self._views = views

    async def execute(self, actor: Actor, post_id: str) -> PostView:
        if await self._repo.get_post(post_id) is None:
            raise PostNotFoundError()
        await self._repo.increment_shares(post_id)
        return await self._views.one(actor, post_id)


class ListCommunitiesUseCase:
    def __init__(self, repo: CommunityRepositoryProtocol):
        self._repo = repo

    async def execute(self, actor: Actor) -> list[CommunityView]:
        counts = await self._repo.member_counts()
        joined = await self._repo.joined_ids(actor.id)
        return [
            CommunityView(c, counts.get(c.id, 0), c.id in joined)
            for c in await self._repo.list_communities()
        ]


class ToggleMembershipUseCase:
    def __init__(self, repo: CommunityRepositoryProtocol):
        self._repo = repo

    async def execute(self, actor: Actor, community_id: str) -> CommunityView:
        community = await self._repo.get_community(community_id)
        if community is None:
            raise CommunityNotFoundError()
        await self._repo.toggle_membership(community.id, actor.id)
        counts = await self._repo.member_counts()
        joined = community.id in await self._repo.joined_ids(actor.id)
        return CommunityView(community, counts.get(community.id, 0), joined)
