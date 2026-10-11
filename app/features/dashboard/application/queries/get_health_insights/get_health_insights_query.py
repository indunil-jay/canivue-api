from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class GetHealthInsightsQuery:
    actor: Actor
    dog_id: str
