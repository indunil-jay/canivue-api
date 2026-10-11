from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class GetNutritionProfileQuery:
    actor: Actor
    dog_id: str
