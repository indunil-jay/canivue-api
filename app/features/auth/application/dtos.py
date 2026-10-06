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
    created_at: datetime
    updated_at: datetime
