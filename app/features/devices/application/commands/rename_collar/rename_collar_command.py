from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class RenameCollarCommand:
    actor: Actor
    dog_id: str
    name: str
