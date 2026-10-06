from dataclasses import dataclass

from app.features.auth.domain.entities import Role


@dataclass(frozen=True)
class CreateStaffUserCommand:
    """Command payload for onboarding a staff user (VET or ADMIN)."""

    email: str
    password: str
    role: Role
    full_name: str | None = None
