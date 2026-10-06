from dataclasses import dataclass

from app.features.auth.domain.entities import Role


@dataclass(frozen=True)
class CreateClientCommand:
    """Command payload for registering a new client account."""

    email: str
    password: str
    full_name: str | None = None
    role: Role = Role.CLIENT
