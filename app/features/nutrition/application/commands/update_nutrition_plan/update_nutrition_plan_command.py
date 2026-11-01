from dataclasses import dataclass
from typing import Any

from app.shared.actor import Actor


@dataclass(frozen=True)
class UpdateNutritionPlanCommand:
    actor: Actor
    dog_id: str
    changes: dict[str, Any]
