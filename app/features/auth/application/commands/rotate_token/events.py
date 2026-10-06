from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class RefreshTokenRotatedEvent:
    """Domain/Application event emitted when a refresh token is successfully rotated."""

    user_id: int
    occurred_at: datetime = field(default_factory=_utc_now)
