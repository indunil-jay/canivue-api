from abc import ABC, abstractmethod

from app.features.auth.domain.entities import RefreshToken


class RefreshTokenRepository(ABC):
    """Abstract interface defining persistence operations for RefreshToken entities."""

    @abstractmethod
    async def create(self, token: RefreshToken) -> RefreshToken: ...

    @abstractmethod
    async def get_by_hash(self, token_hash: str) -> RefreshToken | None: ...

    @abstractmethod
    async def revoke(self, token_hash: str) -> None: ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: int) -> None: ...
