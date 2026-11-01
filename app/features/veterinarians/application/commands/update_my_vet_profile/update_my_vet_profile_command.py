from dataclasses import dataclass
from typing import Any

from app.shared.actor import Actor


@dataclass(frozen=True)
class UpdateMyVetProfileCommand:
    actor: Actor
    changes: dict[str, Any]
