from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseSqlAlchemyRepository
from app.features.sample.domain.entities import SampleItem
from app.features.sample.domain.repositories import SampleRepositoryProtocol
from app.features.sample.infrastructure.models import SampleModel


class SQLAlchemySampleRepository(
    BaseSqlAlchemyRepository[SampleItem, SampleModel, str],
    SampleRepositoryProtocol,
):
    """SQLAlchemy implementation of the SampleRepositoryProtocol."""

    _model_cls = SampleModel

    def __init__(self, session: AsyncSession):
        super().__init__(session=session)

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

    def _to_model_dict(self, entity: SampleItem) -> dict[str, Any]:
        """Convert domain entity to ORM attribute dict."""
        return {
            "id": entity.id,
            "title": entity.title,
            "description": entity.description,
            "is_active": entity.is_active,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    async def get_by_title(self, title: str) -> SampleItem | None:
        query = select(SampleModel).where(SampleModel.title == title)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

