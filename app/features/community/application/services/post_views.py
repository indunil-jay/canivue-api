from collections.abc import Sequence

from app.features.community.application.interfaces.repositories.community_repository import (
    CommunityRepositoryProtocol,
)
from app.features.community.domain.entities.community_post import CommunityPost
from app.features.community.domain.enums.reaction_kind import ReactionKind
from app.features.community.domain.exceptions import PostNotFoundError
from app.features.community.domain.value_objects.post_view import PostView
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
