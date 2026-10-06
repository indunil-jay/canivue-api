from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Generic, TypeVar

TEntity = TypeVar("TEntity")
TId = TypeVar("TId")


class BaseRepositoryProtocol(ABC, Generic[TEntity, TId]):
    """Generic repository interface defining standard persistence operations.

    Domain/application interfaces can inherit from this contract with their entity
    and ID types (e.g. `UserRepository(BaseRepositoryProtocol[User, int])`),
    eliminating boilerplate CRUD signatures.
    """

    @abstractmethod
    async def get_by_id(self, entity_id: TId) -> TEntity | None:
        """Fetch a single entity by its identifier."""
        ...

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> Sequence[TEntity]:
        """List entities with pagination."""
        ...

    @abstractmethod
    async def create(self, entity: TEntity) -> TEntity:
        """Persist a new entity."""
        ...

    @abstractmethod
    async def update(self, entity: TEntity) -> TEntity:
        """Update an existing entity."""
        ...

    @abstractmethod
    async def delete(self, entity_id: TId) -> bool:
        """Delete an entity by its identifier. Returns True if deleted."""
        ...
