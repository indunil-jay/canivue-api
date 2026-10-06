
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.domain.entities import RefreshToken, Role, User
from app.features.auth.domain.repositories import (
    RefreshTokenRepository,
    UserRepository,
)
from app.features.auth.infrastructure.models import RefreshTokenModel, UserModel
from app.features.auth.infrastructure.rbac_repository import SqlAlchemyRbacRepository


class SqlAlchemyUserRepository(UserRepository):
    """SQLAlchemy implementation of the UserRepository interface."""


    def __init__(self, session: AsyncSession, rbac_repo: SqlAlchemyRbacRepository | None = None):
        self._session = session
        self._rbac_repo = rbac_repo or SqlAlchemyRbacRepository(session=session)

    async def _to_entity(self, model: UserModel) -> User:
        role = Role(model.role)
        perms = await self._rbac_repo.get_permissions_for_role(role)
        return User(
            id=model.id,
            email=model.email,
            hashed_password=model.hashed_password,
            role=role,
            full_name=model.full_name,
            is_active=model.is_active,
            permissions=perms,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, user_id: int) -> User | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return await self._to_entity(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email.strip().lower())
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return await self._to_entity(model) if model else None

    async def create(self, user: User) -> User:
        model = UserModel(
            email=user.email,
            hashed_password=user.hashed_password,
            role=user.role.value,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return await self._to_entity(model)

    async def update(self, user: User) -> User:
        stmt = select(UserModel).where(UserModel.id == user.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"User with id {user.id} not found.")

        model.email = user.email
        model.hashed_password = user.hashed_password
        model.role = user.role.value
        model.full_name = user.full_name
        model.is_active = user.is_active
        model.updated_at = user.updated_at

        await self._session.flush()
        await self._session.refresh(model)
        return await self._to_entity(model)



class SqlAlchemyRefreshTokenRepository(RefreshTokenRepository):
    """SQLAlchemy implementation of RefreshTokenRepository interface."""

    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_entity(self, model: RefreshTokenModel) -> RefreshToken:
        return RefreshToken(
            id=model.id,
            user_id=model.user_id,
            token_hash=model.token_hash,
            expires_at=model.expires_at,
            is_revoked=model.is_revoked,
            created_at=model.created_at,
        )

    async def create(self, token: RefreshToken) -> RefreshToken:
        model = RefreshTokenModel(
            user_id=token.user_id,
            token_hash=token.token_hash,
            expires_at=token.expires_at,
            is_revoked=token.is_revoked,
            created_at=token.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def revoke(self, token_hash: str) -> None:
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.is_revoked = True
            await self._session.flush()

    async def revoke_all_for_user(self, user_id: int) -> None:
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.user_id == user_id)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        for m in models:
            m.is_revoked = True
        await self._session.flush()

