
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.domain.entities import Role, User
from app.features.auth.domain.protocols import UserRepositoryProtocol
from app.features.auth.infrastructure.models import UserModel


class SqlAlchemyUserRepository(UserRepositoryProtocol):
    """SQLAlchemy implementation of the UserRepositoryProtocol."""

    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            hashed_password=model.hashed_password,
            role=Role(model.role),
            full_name=model.full_name,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, user_id: int) -> User | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email.strip().lower())
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

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
        return self._to_entity(model)

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
        return self._to_entity(model)
