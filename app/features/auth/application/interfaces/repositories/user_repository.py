from abc import abstractmethod

from app.features.auth.domain.entities.user import User
from app.shared.repository import BaseRepositoryProtocol


class UserRepository(BaseRepositoryProtocol[User, int]):
    """Abstract interface defining persistence operations for User entities."""

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def get_by_google_id(self, google_id: str) -> User | None: ...
