from collections.abc import Sequence

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dataclass_repository import DataclassRepository
from app.features.community.application.interfaces.repositories.community_repository import (
    CommunityRepositoryProtocol,
)
from app.features.community.domain.entities.community_post import CommunityPost
from app.features.community.domain.entities.disease_community import DiseaseCommunity
from app.features.community.domain.enums.reaction_kind import ReactionKind
from app.features.community.infrastructure.persistence.models.community_membership_model import (
    CommunityMembershipModel,
)
from app.features.community.infrastructure.persistence.models.community_post_model import (
    CommunityPostModel,
)
from app.features.community.infrastructure.persistence.models.disease_community_model import (
    DiseaseCommunityModel,
)
from app.features.community.infrastructure.persistence.models.post_reaction_model import (
    PostReactionModel,
)


class _Communities(DataclassRepository[DiseaseCommunity, DiseaseCommunityModel]):
    _model_cls = DiseaseCommunityModel
    _entity_cls = DiseaseCommunity


class _Posts(DataclassRepository[CommunityPost, CommunityPostModel]):
    _model_cls = CommunityPostModel
    _entity_cls = CommunityPost


class SqlAlchemyCommunityRepository(CommunityRepositoryProtocol):
    def __init__(self, session: AsyncSession):
        self._session = session
        self._communities = _Communities(session)
        self._posts = _Posts(session)

    async def _toggle(self, model, **key) -> None:
        """Removes the row with this key if it exists, otherwise adds it."""
        where = [getattr(model, name) == value for name, value in key.items()]
        removed = await self._session.execute(delete(model).where(*where))
        if not removed.rowcount:
            self._session.add(model(**key))
        await self._session.flush()

    async def get_community(self, community_id: str) -> DiseaseCommunity | None:
        return await self._communities.get_by_id(community_id)

    async def list_communities(self) -> Sequence[DiseaseCommunity]:
        return await self._communities.find(order_by=DiseaseCommunityModel.name)

    async def member_counts(self) -> dict[str, int]:
        m = CommunityMembershipModel
        rows = await self._session.execute(
            select(m.community_id, func.count()).group_by(m.community_id)
        )
        return {community_id: count for community_id, count in rows.all()}

    async def joined_ids(self, user_id: int) -> set[str]:
        m = CommunityMembershipModel
        rows = await self._session.execute(select(m.community_id).where(m.user_id == user_id))
        return set(rows.scalars().all())

    async def toggle_membership(self, community_id: str, user_id: int) -> None:
        await self._toggle(CommunityMembershipModel, community_id=community_id, user_id=user_id)

    async def add_post(self, post: CommunityPost) -> CommunityPost:
        return await self._posts.create(post)

    async def get_post(self, post_id: str) -> CommunityPost | None:
        return await self._posts.get_by_id(post_id)

    async def list_posts(
        self, community_id: str | None, saved_by: int | None, limit: int
    ) -> Sequence[CommunityPost]:
        where = []
        if community_id:
            where.append(CommunityPostModel.community_id == community_id)
        if saved_by is not None:
            r = PostReactionModel
            saved = select(r.post_id).where(
                r.user_id == saved_by, r.kind == ReactionKind.SAVE.value
            )
            where.append(CommunityPostModel.id.in_(saved))
        return await self._posts.find(
            *where, order_by=CommunityPostModel.created_at.desc(), limit=limit
        )

    async def like_counts(self, post_ids: Sequence[str]) -> dict[str, int]:
        if not post_ids:
            return {}
        r = PostReactionModel
        rows = await self._session.execute(
            select(r.post_id, func.count())
            .where(r.post_id.in_(post_ids), r.kind == ReactionKind.LIKE.value)
            .group_by(r.post_id)
        )
        return {post_id: count for post_id, count in rows.all()}

    async def reactions_of(self, user_id: int, post_ids: Sequence[str]) -> set[tuple[str, str]]:
        if not post_ids:
            return set()
        r = PostReactionModel
        rows = await self._session.execute(
            select(r.post_id, r.kind).where(r.user_id == user_id, r.post_id.in_(post_ids))
        )
        return {(post_id, kind) for post_id, kind in rows.all()}

    async def toggle_reaction(self, post_id: str, user_id: int, kind: ReactionKind) -> None:
        await self._toggle(PostReactionModel, post_id=post_id, user_id=user_id, kind=kind.value)

    async def increment_shares(self, post_id: str) -> None:
        p = CommunityPostModel
        await self._session.execute(
            update(p).where(p.id == post_id).values(share_count=p.share_count + 1)
        )
        await self._session.flush()
