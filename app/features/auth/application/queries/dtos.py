from dataclasses import dataclass


@dataclass(frozen=True)
class GetCurrentUserQuery:
    """Query to look up an active authenticated user profile by user ID."""

    user_id: int
