from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class UserLoggedInDomainEvent:
    user_id: int
    email: str
    occurred_at: datetime = field(default_factory=_utc_now)
