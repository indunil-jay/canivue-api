from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class GetHealthTimelineQuery:
    actor: Actor
    dog_id: str
