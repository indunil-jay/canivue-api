from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.application.interfaces.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from app.features.auth.domain.entities.password_reset_token import (
    PasswordResetToken,
)
from app.features.auth.infrastructure.models import PasswordResetTokenModel


class SqlAlchemyPasswordResetTokenRepository(PasswordResetTokenRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def _to_entity(self, model: PasswordResetTokenModel) -> PasswordResetToken:
        return PasswordResetToken(
            id=model.id,
            user_id=model.user_id,
            token_hash=model.token_hash,
            expires_at=model.expires_at,
            is_used=model.is_used,
            created_at=model.created_at,
        )

    async def create(self, token: PasswordResetToken) -> PasswordResetToken:
        model = PasswordResetTokenModel(
            user_id=token.user_id,
            token_hash=token.token_hash,
            expires_at=token.expires_at,
            is_used=token.is_used,
            created_at=token.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return await self._to_entity(model)

    async def get_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        stmt = select(PasswordResetTokenModel).where(PasswordResetTokenModel.token_hash == token_hash)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return await self._to_entity(model) if model else None

    async def mark_as_used(self, token_hash: str) -> None:
        stmt = (
            update(PasswordResetTokenModel)
            .where(PasswordResetTokenModel.token_hash == token_hash)
            .values(is_used=True)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def invalidate_all_for_user(self, user_id: int) -> None:
        stmt = (
            update(PasswordResetTokenModel)
            .where(PasswordResetTokenModel.user_id == user_id)
            .values(is_used=True)
        )
        await self._session.execute(stmt)
        await self._session.flush()
