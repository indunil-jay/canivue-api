from typing import Protocol

from app.features.auth.domain.entities.password_reset_token import (
    PasswordResetToken,
)


class PasswordResetTokenRepository(Protocol):
    async def create(self, token: PasswordResetToken) -> PasswordResetToken: ...

    async def get_by_hash(self, token_hash: str) -> PasswordResetToken | None: ...

    async def mark_as_used(self, token_hash: str) -> None: ...

    async def invalidate_all_for_user(self, user_id: int) -> None: ...
