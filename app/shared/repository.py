from typing import Generic, List, Optional, Protocol, TypeVar

T = TypeVar("T")
ID = TypeVar("ID")


class BaseRepositoryProtocol(Protocol[T, ID]):
    """Generic Abstract Base Repository Protocol defining core persistence contracts."""

    async def get_by_id(self, entity_id: ID) -> Optional[T]:
        ...

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        ...

    async def create(self, entity: T) -> T:
        ...

    async def update(self, entity: T) -> T:
        ...

    async def delete(self, entity_id: ID) -> bool:
        ...
