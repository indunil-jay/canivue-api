from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

TEntity = TypeVar("TEntity")
TModel = TypeVar("TModel", bound=Base)
TId = TypeVar("TId")


class BaseSqlAlchemyRepository(Generic[TEntity, TModel, TId]):
    _model_cls: type[TModel]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    def session(self) -> AsyncSession:
        return self._session

    def _to_entity(self, model: TModel) -> TEntity:
        raise NotImplementedError

    def _to_model_dict(self, entity: TEntity) -> dict[str, Any]:
        raise NotImplementedError

    async def get_by_id(self, entity_id: TId) -> TEntity | None:
        stmt = select(self._model_cls).where(self._model_cls.id == entity_id)  # type: ignore[attr-defined]
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        res = self._to_entity(model)
        if hasattr(res, "__await__"):
            return await res  # type: ignore[no-any-return]
        return res

    async def list_all(self, skip: int = 0, limit: int = 100) -> Sequence[TEntity]:
        stmt = select(self._model_cls).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        entities = []
        for m in models:
            e = self._to_entity(m)
            if hasattr(e, "__await__"):
                e = await e
            entities.append(e)
        return entities

    async def create(self, entity: TEntity) -> TEntity:
        model_attrs = self._to_model_dict(entity)
        model = self._model_cls(**model_attrs)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        res = self._to_entity(model)
        if hasattr(res, "__await__"):
            return await res  # type: ignore[no-any-return]
        return res

    async def update(self, entity: TEntity) -> TEntity:
        entity_id = entity.id  # type: ignore[attr-defined]
        stmt = select(self._model_cls).where(self._model_cls.id == entity_id)  # type: ignore[attr-defined]
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return entity

        attrs = self._to_model_dict(entity)
        for key, val in attrs.items():
            if hasattr(model, key):
                setattr(model, key, val)

        await self._session.flush()
        res = self._to_entity(model)
        if hasattr(res, "__await__"):
            return await res  # type: ignore[no-any-return]
        return res

    async def delete(self, entity_id: TId) -> bool:
        stmt = delete(self._model_cls).where(self._model_cls.id == entity_id)  # type: ignore[attr-defined]
        result = await self._session.execute(stmt)
        await self._session.flush()
        return bool(result.rowcount and result.rowcount > 0)
