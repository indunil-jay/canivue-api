from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class ChangePlanCommand:
    actor: Actor
    plan_id: str
