from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class CompleteCareTaskCommand:
    actor: Actor
    dog_id: str
    task_id: str
