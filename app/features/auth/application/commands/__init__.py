from app.features.auth.application.commands.create_client import (
    ClientCreatedEvent,
    ClientCreatedEventHandler,
    CreateClientCommand,
    CreateClientCommandHandler,
)
from app.features.auth.application.commands.create_staff import (
    CreateStaffUserCommand,
    CreateStaffUserCommandHandler,
    StaffUserCreatedEvent,
    StaffUserCreatedEventHandler,
)
from app.features.auth.application.commands.login import (
    LoginResult,
    LoginUserCommand,
    LoginUserCommandHandler,
    UserLoggedInEvent,
    UserLoggedInEventHandler,
)
from app.features.auth.application.commands.rotate_token import (
    RefreshTokenRotatedEvent,
    RefreshTokenRotatedEventHandler,
    RotateRefreshTokenCommand,
    RotateRefreshTokenCommandHandler,
)

# Aliases for smooth backward compatibility
RegisterClientCommand = CreateClientCommand
RegisterClientCommandHandler = CreateClientCommandHandler
LoginCommand = LoginUserCommand
LoginResultDTO = LoginResult

__all__ = [
    "ClientCreatedEvent",
    "ClientCreatedEventHandler",
    # create_client
    "CreateClientCommand",
    "CreateClientCommandHandler",
    # create_staff
    "CreateStaffUserCommand",
    "CreateStaffUserCommandHandler",
    "LoginCommand",
    "LoginResult",
    "LoginResultDTO",
    # login
    "LoginUserCommand",
    "LoginUserCommandHandler",
    "RefreshTokenRotatedEvent",
    "RefreshTokenRotatedEventHandler",
    "RegisterClientCommand",
    "RegisterClientCommandHandler",
    # rotate_token
    "RotateRefreshTokenCommand",
    "RotateRefreshTokenCommandHandler",
    "StaffUserCreatedEvent",
    "StaffUserCreatedEventHandler",
    "UserLoggedInEvent",
    "UserLoggedInEventHandler",
]
