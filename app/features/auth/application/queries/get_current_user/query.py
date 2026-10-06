from dataclasses import dataclass


@dataclass(frozen=True)
class GetCurrentUserQuery:
    """Query payload containing user ID to resolve active profile."""

    user_id: int
