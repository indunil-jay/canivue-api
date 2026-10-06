from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.features.auth.domain.enums.role import Role
from app.features.auth.domain.exceptions import (
    EmptyPasswordHashError,
    InvalidEmailError,
)


@dataclass
class User:
    id: int | None
    email: str
    hashed_password: str | None
    role: Role
    full_name: str | None = None
    google_id: str | None = None
    is_active: bool = True
    permissions: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def validate_email(self) -> None:
        email = self.email.strip().lower()
        if not email or "@" not in email:
            raise InvalidEmailError()

    def validate_password_hash(self) -> None:
        if self.hashed_password is not None and not self.hashed_password:
            raise EmptyPasswordHashError()

    @classmethod
    def create_client(
        cls, email: str, hashed_password: str | None, full_name: str | None = None, google_id: str | None = None
    ) -> "User":
        now = datetime.now(timezone.utc)
        user = cls(
            id=None,
            email=email.strip().lower(),
            hashed_password=hashed_password,
            role=Role.CLIENT,
            full_name=full_name,
            google_id=google_id,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        user.validate_email()
        user.validate_password_hash()
        return user
