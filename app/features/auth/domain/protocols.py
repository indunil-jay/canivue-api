from typing import Protocol

from app.features.auth.domain.entities import RefreshToken, User


class UserRepositoryProtocol(Protocol):
    """Protocol defining persistence seam for User entities."""

    async def get_by_id(self, user_id: int) -> User | None:
        ...

    async def get_by_email(self, email: str) -> User | None:
        ...

    async def create(self, user: User) -> User:
        ...

    async def update(self, user: User) -> User:
        ...


class RefreshTokenRepositoryProtocol(Protocol):
    """Protocol defining persistence seam for RefreshToken entities."""

    async def create(self, token: RefreshToken) -> RefreshToken:
        ...

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        ...

    async def revoke(self, token_hash: str) -> None:
        ...

    async def revoke_all_for_user(self, user_id: int) -> None:
        ...


class RbacRepositoryProtocol(Protocol):
    """Protocol defining persistence and querying of roles and permissions."""

    async def get_permissions_for_role(self, role: str) -> list[str]:
        ...

    async def assign_permission_to_role(self, role: str, permission_name: str) -> None:
        ...

    async def create_permission_if_not_exists(self, name: str, description: str | None = None) -> int:
        ...




class PasswordHasherProtocol(Protocol):
    """Protocol defining secure password hashing seam."""

    def hash(self, password: str) -> str:
        ...

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        ...


class TokenServiceProtocol(Protocol):
    """Protocol defining JWT creation and verification seam."""

    def create_access_token(self, subject: str, role: str) -> str:
        ...

    def create_refresh_token(self, subject: str) -> str:
        ...

    def decode_token(self, token: str) -> dict:
        ...

