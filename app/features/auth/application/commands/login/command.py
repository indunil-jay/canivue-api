from dataclasses import dataclass

from app.features.auth.application.common_dtos import UserOutputDTO


@dataclass(frozen=True)
class LoginUserCommand:
    """Command payload for user authentication."""

    email: str
    password: str


@dataclass(frozen=True)
class LoginResult:
    """Command result payload containing JWT tokens and authenticated user data."""

    access_token: str
    refresh_token: str
    token_type: str
    user: UserOutputDTO
