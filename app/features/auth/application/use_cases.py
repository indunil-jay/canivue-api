from app.features.auth.application.commands.create_staff_user import CreateStaffUserUseCase
from app.features.auth.application.commands.dtos import (
    CreateStaffUserCommand,
    LoginCommand,
    LoginResultDTO,
    RegisterClientCommand,
    RotateRefreshTokenCommand,
)
from app.features.auth.application.commands.login_user import LoginUseCase
from app.features.auth.application.commands.register_client import RegisterClientUseCase
from app.features.auth.application.commands.rotate_refresh_token import RotateRefreshTokenUseCase
from app.features.auth.application.common_dtos import TokenPairOutputDTO, UserOutputDTO
from app.features.auth.application.queries.dtos import GetCurrentUserQuery
from app.features.auth.application.queries.get_current_user import GetCurrentUserUseCase

# Backward-compatibility aliases
RefreshTokenUseCase = RotateRefreshTokenUseCase

__all__ = [
    "CreateStaffUserCommand",
    "CreateStaffUserUseCase",
    "GetCurrentUserQuery",
    "GetCurrentUserUseCase",
    "LoginCommand",
    "LoginResultDTO",
    "LoginUseCase",
    "RefreshTokenUseCase",
    "RegisterClientCommand",
    "RegisterClientUseCase",
    "RotateRefreshTokenCommand",
    "RotateRefreshTokenUseCase",
    "TokenPairOutputDTO",
    "UserOutputDTO",
]
