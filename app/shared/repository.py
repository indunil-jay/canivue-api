from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Generic, TypeVar

TEntity = TypeVar("TEntity")
TId = TypeVar("TId")


class BaseRepositoryProtocol(ABC, Generic[TEntity, TId]):
    @abstractmethod
    async def get_by_id(self, entity_id: TId) -> TEntity | None: ...

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> Sequence[TEntity]: ...

    @abstractmethod
    async def create(self, entity: TEntity) -> TEntity: ...

    @abstractmethod
    async def update(self, entity: TEntity) -> TEntity: ...

    @abstractmethod
    async def delete(self, entity_id: TId) -> bool: ...
