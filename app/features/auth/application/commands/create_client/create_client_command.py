from dataclasses import dataclass

from app.features.auth.domain.enums.role import Role


@dataclass(frozen=True)
class CreateClientCommand:
    email: str
    password: str
    full_name: str | None = None
    role: Role = Role.CLIENT
