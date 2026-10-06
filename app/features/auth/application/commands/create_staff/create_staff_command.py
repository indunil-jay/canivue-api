from dataclasses import dataclass

from app.features.auth.domain.enums.role import Role


@dataclass(frozen=True)
class CreateStaffCommand:
    email: str
    password: str
    role: Role
    full_name: str | None = None
