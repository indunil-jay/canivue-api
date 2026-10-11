from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class GetFeedQuery:
    actor: Actor
    community_id: str | None
    saved_only: bool
    limit: int
