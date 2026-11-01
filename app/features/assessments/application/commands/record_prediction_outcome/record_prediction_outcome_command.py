from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class RecordPredictionOutcomeCommand:
    actor: Actor
    dog_id: str
    prediction_id: str
    outcome_note: str
    resolved: bool
