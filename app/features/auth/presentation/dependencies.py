from collections.abc import Callable

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.features.auth.application.commands.create_client.create_client_command_handler import (
    CreateClientCommandHandler,
)
from app.features.auth.application.commands.create_staff.create_staff_command_handler import (
    CreateStaffCommandHandler,
)
from app.features.auth.application.commands.login.login_user_command_handler import (
    LoginUserCommandHandler,
)
from app.features.auth.application.commands.rotate_token.rotate_refresh_token_command_handler import (
    RotateRefreshTokenCommandHandler,
)
from app.features.auth.application.dtos.user_output_dto import UserOutputDTO
from app.features.auth.application.exceptions import (
    InsufficientPermissionsError,
    InvalidCredentialsError,
)
from app.features.auth.application.interfaces.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from app.features.auth.application.interfaces.repositories.user_repository import (
    UserRepository,
)
from app.features.auth.application.interfaces.services.password_hasher import (
    PasswordHasher,
)
from app.features.auth.application.interfaces.services.token_service import (
    TokenService,
)
from app.features.auth.application.queries.get_current_user.get_current_user_query import (
    GetCurrentUserQuery,
)
from app.features.auth.application.queries.get_current_user.get_current_user_query_handler import (
    GetCurrentUserQueryHandler,
)
from app.features.auth.domain.enums.role import Role
from app.features.auth.infrastructure.repositories.refresh_token_repository import (
    SqlAlchemyRefreshTokenRepository,
)
from app.features.auth.infrastructure.repositories.user_repository import (
    SqlAlchemyUserRepository,
)
from app.features.auth.infrastructure.services.hasher import Argon2PasswordHasher
from app.features.auth.infrastructure.services.token_service import JwtTokenService

_hasher_instance = Argon2PasswordHasher()
_token_service_instance = JwtTokenService()


def get_password_hasher() -> PasswordHasher:
    return _hasher_instance


def get_token_service() -> TokenService:
    return _token_service_instance


def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    return SqlAlchemyUserRepository(session=session)


def get_refresh_token_repository(
    session: AsyncSession = Depends(get_db_session),
) -> RefreshTokenRepository:
    return SqlAlchemyRefreshTokenRepository(session=session)


def get_create_client_command_handler(
    user_repo: UserRepository = Depends(get_user_repository),
    hasher: PasswordHasher = Depends(get_password_hasher),
) -> CreateClientCommandHandler:
    return CreateClientCommandHandler(user_repo=user_repo, hasher=hasher)


def get_create_staff_command_handler(
    user_repo: UserRepository = Depends(get_user_repository),
    hasher: PasswordHasher = Depends(get_password_hasher),
) -> CreateStaffCommandHandler:
    return CreateStaffCommandHandler(user_repo=user_repo, hasher=hasher)


def get_login_command_handler(
    user_repo: UserRepository = Depends(get_user_repository),
    hasher: PasswordHasher = Depends(get_password_hasher),
    token_service: TokenService = Depends(get_token_service),
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
) -> LoginUserCommandHandler:
    return LoginUserCommandHandler(
        user_repo=user_repo,
        hasher=hasher,
        token_service=token_service,
        refresh_token_repo=refresh_token_repo,
    )


def get_rotate_token_command_handler(
    user_repo: UserRepository = Depends(get_user_repository),
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
    token_service: TokenService = Depends(get_token_service),
) -> RotateRefreshTokenCommandHandler:
    return RotateRefreshTokenCommandHandler(
        user_repo=user_repo,
        refresh_token_repo=refresh_token_repo,
        token_service=token_service,
    )


def get_current_user_query_handler(
    user_repo: UserRepository = Depends(get_user_repository),
) -> GetCurrentUserQueryHandler:
    return GetCurrentUserQueryHandler(user_repo=user_repo)


async def get_current_user(
    authorization: str | None = Header(None, alias="Authorization"),
    token_service: TokenService = Depends(get_token_service),
    query_handler: GetCurrentUserQueryHandler = Depends(get_current_user_query_handler),
) -> UserOutputDTO:
    """Security seam extracting Bearer JWT and resolving active user."""
    if not authorization:
        raise InvalidCredentialsError("Missing authorization header.")

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise InvalidCredentialsError("Invalid authorization scheme. Use 'Bearer <token>'.")

    token = parts[1]
    payload = token_service.decode_token(token)

    if payload.get("type") != "access":
        raise InvalidCredentialsError("Invalid token type. Access token required.")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise InvalidCredentialsError("Invalid token claims.")

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError) as e:
        raise InvalidCredentialsError("Invalid subject claim in token.") from e

    query = GetCurrentUserQuery(user_id=user_id)
    return await query_handler.handle(query)


def require_roles(*allowed_roles: Role | str) -> Callable:
    """Dependency factory checking that caller has one of the allowed roles."""
    roles = {r.value if isinstance(r, Role) else str(r) for r in allowed_roles}

    async def _role_guard(current_user: UserOutputDTO = Depends(get_current_user)) -> UserOutputDTO:
        if current_user.role.value not in roles:
            raise InsufficientPermissionsError(
                f"Action requires one of the following roles: {', '.join(sorted(roles))}."
            )
        return current_user

    return _role_guard


def require_permissions(*required_permissions: str) -> Callable:
    """Dependency factory checking that caller possesses all required permissions."""

    async def _permission_guard(
        current_user: UserOutputDTO = Depends(get_current_user),
    ) -> UserOutputDTO:
        user_perms = set(current_user.permissions)
        missing = [p for p in required_permissions if p not in user_perms]
        if missing:
            raise InsufficientPermissionsError(
                f"Missing required permission(s): {', '.join(missing)}."
            )
        return current_user

    return _permission_guard
