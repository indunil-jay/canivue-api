from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class ToggleMembershipCommand:
    actor: Actor
    community_id: str
