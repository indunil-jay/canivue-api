from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.features.auth.application.use_cases import RegisterClientUseCase
from app.features.auth.domain.protocols import PasswordHasherProtocol, UserRepositoryProtocol
from app.features.auth.infrastructure.hasher import Argon2PasswordHasher
from app.features.auth.infrastructure.repository import SqlAlchemyUserRepository

_hasher_instance = Argon2PasswordHasher()


def get_password_hasher() -> PasswordHasherProtocol:
    return _hasher_instance


def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> UserRepositoryProtocol:
    return SqlAlchemyUserRepository(session=session)


def get_register_client_use_case(
    user_repo: UserRepositoryProtocol = Depends(get_user_repository),
    hasher: PasswordHasherProtocol = Depends(get_password_hasher),
) -> RegisterClientUseCase:
    return RegisterClientUseCase(user_repo=user_repo, hasher=hasher)
