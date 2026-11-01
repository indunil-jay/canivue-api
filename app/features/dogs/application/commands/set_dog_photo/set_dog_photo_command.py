from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class SetDogPhotoCommand:
    actor: Actor
    dog_id: str
    content: bytes
    content_type: str | None
    max_bytes: int
