from abc import ABC, abstractmethod

from app.features.auth.domain.entities import RefreshToken, User


class UserRepository(ABC):
    """Abstract Repository interface defining persistence operations for User entities."""

    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None:
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        ...

    @abstractmethod
    async def create(self, user: User) -> User:
        ...

    @abstractmethod
    async def update(self, user: User) -> User:
        ...


class RefreshTokenRepository(ABC):
    """Abstract Repository interface defining persistence operations for RefreshToken entities."""

    @abstractmethod
    async def create(self, token: RefreshToken) -> RefreshToken:
        ...

    @abstractmethod
    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        ...

    @abstractmethod
    async def revoke(self, token_hash: str) -> None:
        ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: int) -> None:
        ...


class RbacRepository(ABC):
    """Abstract Repository interface defining role and permission database operations."""

    @abstractmethod
    async def get_permissions_for_role(self, role: str) -> list[str]:
        ...

    @abstractmethod
    async def assign_permission_to_role(self, role: str, permission_name: str) -> None:
        ...

    @abstractmethod
    async def create_permission_if_not_exists(self, name: str, description: str | None = None) -> int:
        ...
