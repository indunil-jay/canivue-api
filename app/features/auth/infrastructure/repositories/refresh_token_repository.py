from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.application.interfaces.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from app.features.auth.domain.entities import RefreshToken
from app.features.auth.infrastructure.models import RefreshTokenModel


class SqlAlchemyRefreshTokenRepository(RefreshTokenRepository):
    """SQLAlchemy implementation of RefreshTokenRepository interface."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, token: RefreshToken) -> RefreshToken:
        model = RefreshTokenModel(
            user_id=token.user_id,
            token_hash=token.token_hash,
            expires_at=token.expires_at,
            is_revoked=token.is_revoked,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)

        return RefreshToken(
            id=model.id,
            user_id=model.user_id,
            token_hash=model.token_hash,
            expires_at=model.expires_at,
            is_revoked=model.is_revoked,
            created_at=model.created_at,
        )

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None

        return RefreshToken(
            id=model.id,
            user_id=model.user_id,
            token_hash=model.token_hash,
            expires_at=model.expires_at,
            is_revoked=model.is_revoked,
            created_at=model.created_at,
        )

    async def revoke(self, token_hash: str) -> None:
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.is_revoked = True
            await self._session.flush()

    async def revoke_all_for_user(self, user_id: int) -> None:
        stmt = select(RefreshTokenModel).where(
            RefreshTokenModel.user_id == user_id,
            RefreshTokenModel.is_revoked == False,
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        for m in models:
            m.is_revoked = True
        await self._session.flush()
