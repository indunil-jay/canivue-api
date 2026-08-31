from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.sample.domain.entities import SampleItem
from app.features.sample.domain.repositories import SampleRepositoryProtocol
from app.features.sample.infrastructure.models import SampleModel


class SQLAlchemySampleRepository(SampleRepositoryProtocol):
    """SQLAlchemy implementation of the SampleRepositoryProtocol."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: SampleModel) -> SampleItem:
        """Map ORM model to Domain Entity."""
        return SampleItem(
            id=model.id,
            title=model.title,
            description=model.description,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, sample_id: str) -> Optional[SampleItem]:
        query = select(SampleModel).where(SampleModel.id == sample_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_title(self, title: str) -> Optional[SampleItem]:
        query = select(SampleModel).where(SampleModel.title == title)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[SampleItem]:
        query = select(SampleModel).offset(skip).limit(limit)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def create(self, item: SampleItem) -> SampleItem:
        model = SampleModel(
            id=item.id,
            title=item.title,
            description=item.description,
            is_active=item.is_active,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def update(self, item: SampleItem) -> SampleItem:
        query = select(SampleModel).where(SampleModel.id == item.id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        if model:
            model.title = item.title
            model.description = item.description
            model.is_active = item.is_active
            model.updated_at = item.updated_at
            await self.session.flush()
            return self._to_entity(model)
        return item

    async def delete(self, sample_id: str) -> bool:
        stmt = delete(SampleModel).where(SampleModel.id == sample_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
