from dataclasses import dataclass
from datetime import datetime

from app.features.auth.domain.enums.role import Role


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
