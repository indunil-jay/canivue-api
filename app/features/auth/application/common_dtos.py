from dataclasses import dataclass
from datetime import datetime

from app.features.auth.domain.entities import Role


@dataclass(frozen=True)
class UserOutputDTO:
    """Standardized User DTO for cross-use-case output and presentation mapping."""

    id: int
    email: str
    role: Role
    full_name: str | None
    is_active: bool
    permissions: list[str]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class TokenPairOutputDTO:
    """Standardized Token Pair DTO for access and refresh token outputs."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
