from dataclasses import dataclass
from datetime import datetime

from app.features.auth.domain.entities import Role


@dataclass(frozen=True)
class RegisterClientInputDTO:
    email: str
    password: str
    full_name: str | None = None


@dataclass(frozen=True)
class UserOutputDTO:
    id: int
    email: str
    role: Role
    full_name: str | None
    is_active: bool
    permissions: list[str]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class CreateStaffInputDTO:
    email: str
    password: str
    role: Role
    full_name: str | None = None



@dataclass(frozen=True)
class LoginInputDTO:
    email: str
    password: str


@dataclass(frozen=True)
class LoginOutputDTO:
    access_token: str
    refresh_token: str
    token_type: str
    user: UserOutputDTO


@dataclass(frozen=True)
class RefreshTokenInputDTO:
    refresh_token: str


@dataclass(frozen=True)
class TokenPairOutputDTO:
    access_token: str
    refresh_token: str
    token_type: str


