from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.features.auth.domain.entities import Role


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class StaffUserCreatedEvent:
    """Domain/Application event emitted when a new staff user account is created."""

    user_id: int | None
    email: str
    role: Role
    full_name: str | None
    occurred_at: datetime = field(default_factory=_utc_now)
