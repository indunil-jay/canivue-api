from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class GetPredictionQuery:
    actor: Actor
    dog_id: str
    prediction_id: str
