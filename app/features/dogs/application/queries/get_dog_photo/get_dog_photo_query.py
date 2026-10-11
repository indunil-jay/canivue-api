from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class GetDogPhotoQuery:
    actor: Actor
    dog_id: str
