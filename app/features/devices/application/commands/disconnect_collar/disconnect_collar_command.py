from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class DisconnectCollarCommand:
    actor: Actor
    dog_id: str
