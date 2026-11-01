from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class RemoveDogCommand:
    actor: Actor
    dog_id: str
