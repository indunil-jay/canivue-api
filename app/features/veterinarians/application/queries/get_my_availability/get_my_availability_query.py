from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class GetMyAvailabilityQuery:
    actor: Actor
