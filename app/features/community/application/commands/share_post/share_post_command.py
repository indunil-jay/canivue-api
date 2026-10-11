from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class SharePostCommand:
    actor: Actor
    post_id: str
