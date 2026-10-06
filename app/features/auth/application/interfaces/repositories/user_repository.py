from abc import ABC, abstractmethod

from app.features.auth.domain.entities.user import User


class UserRepository(ABC):
    """Abstract interface defining persistence operations for User entities."""

    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def create(self, user: User) -> User: ...

    @abstractmethod
    async def update(self, user: User) -> User: ...
