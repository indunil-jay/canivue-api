from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.community.domain.constants import DEFAULT_COMMUNITIES
from app.features.community.infrastructure.persistence.models.disease_community_model import (
    DiseaseCommunityModel,
)


async def seed_communities(session: AsyncSession) -> None:
    """Adds the default disease communities that are not there yet."""
    existing = set((await session.execute(select(DiseaseCommunityModel.id))).scalars().all())
    session.add_all(
        DiseaseCommunityModel(id=community_id, name=name, description=description)
        for community_id, name, description in DEFAULT_COMMUNITIES
        if community_id not in existing
    )
    await session.flush()
