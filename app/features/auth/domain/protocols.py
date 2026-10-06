from typing import Protocol

from app.features.auth.domain.entities import User


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


class PasswordHasherProtocol(Protocol):
    """Protocol defining secure password hashing seam."""

    def hash(self, password: str) -> str:
        ...

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        ...
