from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class ListDogAppointmentsQuery:
    actor: Actor
    dog_id: str
