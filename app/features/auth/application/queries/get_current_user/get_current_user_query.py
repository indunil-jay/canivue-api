from dataclasses import dataclass


@dataclass(frozen=True)
class GetCurrentUserQuery:
    user_id: int
