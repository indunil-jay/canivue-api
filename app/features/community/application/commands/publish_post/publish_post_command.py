from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class PublishPostCommand:
    actor: Actor
    community_id: str
    content: str
