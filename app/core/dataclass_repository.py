import types
from collections.abc import Sequence
from dataclasses import fields
from enum import Enum
from typing import Any, Generic, TypeVar, Union, get_args, get_origin, get_type_hints

from sqlalchemy import func, select

from app.core.database import Base
from app.core.repository import BaseSqlAlchemyRepository

TEntity = TypeVar("TEntity")
TModel = TypeVar("TModel", bound=Base)


def _enum_type(hint: Any) -> type[Enum] | None:
    candidates = get_args(hint) if get_origin(hint) in (Union, types.UnionType) else (hint,)
    for candidate in candidates:
        if isinstance(candidate, type) and issubclass(candidate, Enum):
            return candidate
    return None


class DataclassRepository(BaseSqlAlchemyRepository[TEntity, TModel, str], Generic[TEntity, TModel]):
    """Maps a dataclass entity onto a model with the same column names, field for field."""

    _entity_cls: type[TEntity]

    def _to_entity(self, model: TModel) -> TEntity:
        hints = get_type_hints(self._entity_cls)
        values = {}
        for f in fields(self._entity_cls):  # type: ignore[arg-type]
            value = getattr(model, f.name)
            enum_cls = _enum_type(hints[f.name])
            values[f.name] = enum_cls(value) if enum_cls and value is not None else value
        return self._entity_cls(**values)

    def _to_model_dict(self, entity: TEntity) -> dict[str, Any]:
        return {
            f.name: v.value if isinstance(v := getattr(entity, f.name), Enum) else v
            for f in fields(entity)  # type: ignore[arg-type]
        }

    async def find(
        self, *where: Any, order_by: Any = None, limit: int | None = None
    ) -> Sequence[TEntity]:
        stmt = select(self._model_cls).where(*where)
        if order_by is not None:
            stmt = (
                stmt.order_by(*order_by)
                if isinstance(order_by, (list, tuple))
                else stmt.order_by(order_by)
            )
        if limit is not None:
            stmt = stmt.limit(limit)
        return [self._to_entity(m) for m in (await self._session.execute(stmt)).scalars().all()]

    async def find_one(self, *where: Any, order_by: Any = None) -> TEntity | None:
        found = await self.find(*where, order_by=order_by, limit=1)
        return found[0] if found else None

    async def count(self, *where: Any) -> int:
        stmt = select(func.count()).select_from(self._model_cls).where(*where)
        return int((await self._session.execute(stmt)).scalar_one())
