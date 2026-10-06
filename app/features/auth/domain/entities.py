from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class Role(str, Enum):
    ADMIN = "ADMIN"
    VET = "VET"
    CLIENT = "CLIENT"


@dataclass
class User:
    """Pure domain entity representing a system user."""
    id: int | None
    email: str
    hashed_password: str
    role: Role
    full_name: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def create_client(cls, email: str, hashed_password: str, full_name: str | None = None) -> "User":
        """Factory method guaranteeing new clients are created with CLIENT role."""
        now = datetime.now(timezone.utc)
        return cls(
            id=None,
            email=email.strip().lower(),
            hashed_password=hashed_password,
            role=Role.CLIENT,
            full_name=full_name,
            is_active=True,
            created_at=now,
            updated_at=now,
        )


@dataclass
class RefreshToken:
    """Pure domain entity representing a persisted refresh token."""
    id: int | None
    user_id: int
    token_hash: str
    expires_at: datetime
    is_revoked: bool = False
    created_at: datetime | None = None

