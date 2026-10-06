from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.application.interfaces.repositories.user_repository import (
    UserRepository,
)
from app.features.auth.domain.entities import Role, User
from app.features.auth.infrastructure.models import UserModel
from app.features.auth.infrastructure.repositories.rbac_repository import (
    SqlAlchemyRbacRepository,
)


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
        stmt = select(UserModel).where(UserModel.email == email.lower())
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return await self._to_entity(model) if model else None

    async def create(self, user: User) -> User:
        model = UserModel(
            email=user.email.lower(),
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
        model = result.scalar_one()

        model.email = user.email.lower()
        model.hashed_password = user.hashed_password
        model.role = user.role.value
        model.full_name = user.full_name
        model.is_active = user.is_active
        model.updated_at = user.updated_at

        await self._session.flush()
        return await self._to_entity(model)
