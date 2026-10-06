from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseSqlAlchemyRepository
from app.features.auth.application.interfaces.repositories.user_repository import (
    UserRepository,
)
from app.features.auth.domain.entities.user import User
from app.features.auth.domain.enums.role import Role
from app.features.auth.infrastructure.models.user_model import UserModel
from app.features.auth.infrastructure.repositories.rbac_repository import (
    SqlAlchemyRbacRepository,
)


class SqlAlchemyUserRepository(
    BaseSqlAlchemyRepository[User, UserModel, int],
    UserRepository,
):
    """SQLAlchemy implementation of the UserRepository interface."""

    _model_cls = UserModel

    def __init__(self, session: AsyncSession, rbac_repo: SqlAlchemyRbacRepository | None = None):
        super().__init__(session=session)
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
            google_id=model.google_id,
            is_active=model.is_active,
            permissions=perms,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model_dict(self, entity: User) -> dict[str, Any]:
        return {
            "email": entity.email.lower(),
            "hashed_password": entity.hashed_password,
            "role": entity.role.value if isinstance(entity.role, Role) else entity.role,
            "full_name": entity.full_name,
            "google_id": entity.google_id,
            "is_active": entity.is_active,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email.lower())
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return await self._to_entity(model) if model else None

    async def get_by_google_id(self, google_id: str) -> User | None:
        stmt = select(UserModel).where(UserModel.google_id == google_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return await self._to_entity(model) if model else None

