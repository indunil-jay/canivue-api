from dataclasses import dataclass

from app.features.auth.application.common_dtos import UserOutputDTO
from app.features.auth.domain.entities import Role


@dataclass(frozen=True)
class RegisterClientCommand:
    """Command to self-register a new pet owner client."""

    email: str
    password: str
    full_name: str | None = None


@dataclass(frozen=True)
class CreateStaffUserCommand:
    """Command to provision an internal staff account (VET or ADMIN)."""

    email: str
    password: str
    role: Role
    full_name: str | None = None


@dataclass(frozen=True)
class LoginCommand:
    """Command to authenticate credentials and issue tokens."""

    email: str
    password: str


@dataclass(frozen=True)
class LoginResultDTO:
    """Result of executing LoginCommand."""

    access_token: str
    refresh_token: str
    token_type: str
    user: UserOutputDTO


@dataclass(frozen=True)
class RotateRefreshTokenCommand:
    """Command to rotate an active refresh token."""

    refresh_token: str
