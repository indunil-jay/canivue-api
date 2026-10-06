from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class UserRegisteredDomainEvent:
    user_id: int | None
    email: str
    full_name: str | None
    occurred_at: datetime = field(default_factory=_utc_now)
