from abc import abstractmethod

from app.features.auth.domain.entities.user import User
from app.shared.repository import BaseRepositoryProtocol


class UserRepository(BaseRepositoryProtocol[User, int]):
    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def get_by_google_id(self, google_id: str) -> User | None: ...
