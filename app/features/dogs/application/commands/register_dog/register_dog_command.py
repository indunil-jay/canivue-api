from dataclasses import dataclass
from typing import Any

from app.shared.actor import Actor


@dataclass(frozen=True)
class RegisterDogCommand:
    actor: Actor
    attributes: dict[str, Any]
